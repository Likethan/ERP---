"""CampusOS Threat Detection Engine & Security Event Normalization (Step 33).

Provides:
- Normalized security event schema
- Explainable deterministic threat detection rules
- Event evaluation, threshold evaluation, and sliding window aggregation
- Deduplication and alert fatigue prevention
- Automatic security incident grouping
"""

import hashlib
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.sanitizer import mask_sensitive_dict
from app.models.security_ops import (
    SecurityDetection,
    SecurityDetectionRuleConfig,
    SecurityIncident,
    SecurityIncidentNote,
    SecurityResponseAction,
)


class NormalizedSecurityEvent(BaseModel):
    """Normalized security event ingested from audit logs, auth layer, or gateway sensors."""

    id: UUID = Field(default_factory=uuid4)
    event_type: str  # AUTH_LOGIN_FAILED, CROSS_TENANT_ATTEMPT, PERMISSION_DENIED, etc.
    detection_source: str  # AUTH_GATEWAY, AUDIT_MONITOR, RATE_LIMITER, API_GATEWAY, INTEGRATION_BUS
    tenant_id: UUID | None = None
    actor_type: str = "USER"  # USER, API_KEY, SYSTEM, ANONYMOUS
    actor_id: str | None = None  # user_id or client_id string
    target_resource_type: str | None = None  # StudentProfile, ExamResult, Tenant, ApiKey
    target_resource_id: str | None = None
    ip_address: str = "unknown"
    request_id: str = "-"
    audit_log_id: UUID | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ThreatDetectionRule:
    """Deterministic threat detection rule definition."""

    rule_id: str
    version: str
    name: str
    description: str
    category: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    confidence: str  # CONFIRMED, HIGH, MEDIUM, LOW
    evaluation_window_seconds: int
    threshold: int
    recommended_action: str | None = None
    default_enabled: bool = True


# Pre-configured standard enterprise detection rules
STANDARD_RULES: dict[str, ThreatDetectionRule] = {
    "RULE-AUTH-001": ThreatDetectionRule(
        rule_id="RULE-AUTH-001",
        version="1.0.0",
        name="Repeated Authentication Failures",
        description="Detects multiple consecutive login failures against a single account or from a single IP.",
        category="AUTHENTICATION",
        severity="HIGH",
        confidence="HIGH",
        evaluation_window_seconds=600,
        threshold=5,
        recommended_action="RATE_LIMIT_IP",
    ),
    "RULE-AUTH-002": ThreatDetectionRule(
        rule_id="RULE-AUTH-002",
        version="1.0.0",
        name="Distributed Credential Stuffing",
        description="Detects an IP address targeting multiple distinct accounts with failed authentication.",
        category="AUTHENTICATION",
        severity="CRITICAL",
        confidence="HIGH",
        evaluation_window_seconds=600,
        threshold=3,
        recommended_action="RATE_LIMIT_IP",
    ),
    "RULE-TENANT-001": ThreatDetectionRule(
        rule_id="RULE-TENANT-001",
        version="1.0.0",
        name="Cross-Tenant Boundary Access Violation",
        description="Detects deliberate attempts to query or mutate records belonging to a different tenant.",
        category="TENANT_BOUNDARY",
        severity="CRITICAL",
        confidence="CONFIRMED",
        evaluation_window_seconds=300,
        threshold=1,
        recommended_action="REVOKE_SESSION",
    ),
    "RULE-AUTHZ-001": ThreatDetectionRule(
        rule_id="RULE-AUTHZ-001",
        version="1.0.0",
        name="Authorization Failure Spike",
        description="Detects repeated HTTP 403 Forbidden responses indicating permission enumeration.",
        category="AUTHORIZATION",
        severity="HIGH",
        confidence="MEDIUM",
        evaluation_window_seconds=300,
        threshold=10,
        recommended_action="REVOKE_SESSION",
    ),
    "RULE-PRIV-001": ThreatDetectionRule(
        rule_id="RULE-PRIV-001",
        version="1.0.0",
        name="Suspicious Administrative Privilege Escalation",
        description="Detects sensitive role assignments (SUPER_ADMIN, INSTITUTION_ADMIN) outside standard workflows.",
        category="PRIVILEGE",
        severity="HIGH",
        confidence="CONFIRMED",
        evaluation_window_seconds=600,
        threshold=1,
        recommended_action="CREATE_REMEDIATION_TASK",
    ),
    "RULE-API-001": ThreatDetectionRule(
        rule_id="RULE-API-001",
        version="1.0.0",
        name="Repeated API Key Authentication Failures",
        description="Detects rapid authentication or signature verification failures on developer API credentials.",
        category="API",
        severity="HIGH",
        confidence="HIGH",
        evaluation_window_seconds=300,
        threshold=5,
        recommended_action="RATE_LIMIT_IP",
    ),
    "RULE-DATA-001": ThreatDetectionRule(
        rule_id="RULE-DATA-001",
        version="1.0.0",
        name="Excessive Bulk Record Export",
        description="Detects anomalous bulk data export or exfiltration attempts exceeding safe thresholds.",
        category="DATA_ACCESS",
        severity="HIGH",
        confidence="MEDIUM",
        evaluation_window_seconds=300,
        threshold=3,
        recommended_action="REVOKE_SESSION",
    ),
    "RULE-INTEG-001": ThreatDetectionRule(
        rule_id="RULE-INTEG-001",
        version="1.0.0",
        name="Security-Relevant Integration Failure",
        description="Detects webhook signature verification failures or external connector authentication breaches.",
        category="INTEGRATION",
        severity="MEDIUM",
        confidence="HIGH",
        evaluation_window_seconds=600,
        threshold=5,
        recommended_action="CREATE_REMEDIATION_TASK",
    ),
    "RULE-DOC-001": ThreatDetectionRule(
        rule_id="RULE-DOC-001",
        version="1.0.0",
        name="Abnormal Document Download Spike",
        description="Detects rapid batch download of sensitive documents, transcripts, or certificates.",
        category="DATA_ACCESS",
        severity="HIGH",
        confidence="MEDIUM",
        evaluation_window_seconds=300,
        threshold=20,
        recommended_action="REVOKE_SESSION",
    ),
}


class ThreatDetectionEngine:
    """In-memory sliding window evaluator backed by database persistence and incident management."""

    def __init__(self):
        # Sliding window state: rule_id -> key -> deque of timestamps
        self._sliding_windows: dict[str, dict[str, deque[datetime]]] = defaultdict(
            lambda: defaultdict(deque)
        )
        # Targeted accounts per IP: ip -> set of target usernames/emails
        self._ip_targeted_accounts: dict[str, set[str]] = defaultdict(set)

    def _generate_fingerprint(
        self, tenant_id: UUID | None, rule_id: str, actor_key: str
    ) -> str:
        """Create deterministic fingerprint for deduplication."""
        raw = f"{tenant_id or 'platform'}:{rule_id}:{actor_key}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

    async def _get_next_incident_number(self, db: AsyncSession) -> str:
        """Generate human-readable sequential incident number SEC-YYYY-XXXX."""
        year = datetime.now(UTC).year
        prefix = f"SEC-{year}-"
        stmt = (
            select(SecurityIncident.incident_number)
            .where(SecurityIncident.incident_number.like(f"{prefix}%"))
            .order_by(SecurityIncident.incident_number.desc())
            .limit(1)
        )
        latest = (await db.execute(stmt)).scalar_one_or_none()
        if latest:
            try:
                num = int(latest.split("-")[-1]) + 1
            except (ValueError, IndexError):
                num = 1
        else:
            num = 1
        return f"{prefix}{num:04d}"

    async def process_event(
        self,
        db: AsyncSession,
        event: NormalizedSecurityEvent,
    ) -> SecurityDetection | None:
        """Evaluate normalized event against detection rules, record detections, and group incidents."""
        sanitized_details = mask_sensitive_dict(event.details)
        now = event.timestamp

        # Map event_type to potential matching rules
        target_rule_ids: list[str] = []
        if event.event_type in ("AUTH_LOGIN_FAILED", "AUTH_BRUTE_FORCE_SUSPECTED"):
            target_rule_ids.extend(["RULE-AUTH-001", "RULE-AUTH-002"])
        elif event.event_type in ("CROSS_TENANT_ATTEMPT", "SECURITY_ACCESS_DENIED"):
            target_rule_ids.append("RULE-TENANT-001")
        elif event.event_type == "PERMISSION_DENIED_SPIKE":
            target_rule_ids.append("RULE-AUTHZ-001")
        elif event.event_type == "PRIVILEGE_ESCALATION_SUSPECTED":
            target_rule_ids.append("RULE-PRIV-001")
        elif event.event_type == "API_KEY_AUTH_FAILED":
            target_rule_ids.append("RULE-API-001")
        elif event.event_type == "BULK_EXPORT_ANOMALY":
            target_rule_ids.append("RULE-DATA-001")
        elif event.event_type == "INTEGRATION_SECURITY_FAILURE":
            target_rule_ids.append("RULE-INTEG-001")
        elif event.event_type == "DOCUMENT_DOWNLOAD_SPIKE":
            target_rule_ids.append("RULE-DOC-001")

        if not target_rule_ids:
            return None

        # Check DB rule configurations for overrides / enabled status
        rule_configs_stmt = select(SecurityDetectionRuleConfig).where(
            SecurityDetectionRuleConfig.rule_id.in_(target_rule_ids)
        )
        db_configs = {r.rule_id: r for r in (await db.execute(rule_configs_stmt)).scalars().all()}

        triggered_detection: SecurityDetection | None = None

        for rule_id in target_rule_ids:
            rule = STANDARD_RULES.get(rule_id)
            if not rule:
                continue

            config = db_configs.get(rule_id)
            if config and not config.is_enabled:
                continue

            window_seconds = config.evaluation_window_seconds if config else rule.evaluation_window_seconds
            threshold = config.threshold if config else rule.threshold
            severity = config.severity if config else rule.severity

            # Determine grouping key for sliding window
            if rule_id == "RULE-AUTH-002":
                # Credential stuffing: track distinct targets per IP
                target_account = sanitized_details.get("target_account") or sanitized_details.get("email") or "unknown"
                self._ip_targeted_accounts[event.ip_address].add(str(target_account))
                count = len(self._ip_targeted_accounts[event.ip_address])
                actor_key = event.ip_address
            elif rule_id == "RULE-TENANT-001":
                count = 1
                actor_key = event.actor_id or event.ip_address
            else:
                actor_key = event.actor_id or event.ip_address
                window = self._sliding_windows[rule_id][actor_key]
                # Prune older entries
                cutoff = now - timedelta(seconds=window_seconds)
                while window and window[0] < cutoff:
                    window.popleft()
                window.append(now)
                count = len(window)

            if count < threshold:
                continue

            # Rule triggered! Compute fingerprint
            fingerprint = self._generate_fingerprint(event.tenant_id, rule_id, actor_key)

            # Check if an existing unclosed detection exists for this fingerprint
            existing_det_stmt = (
                select(SecurityDetection)
                .where(
                    and_(
                        SecurityDetection.dedup_fingerprint == fingerprint,
                        SecurityDetection.status.in_(["UNTRIAGED", "LINKED_TO_INCIDENT"]),
                    )
                )
                .order_by(SecurityDetection.last_seen_at.desc())
                .limit(1)
            )
            existing_detection = (await db.execute(existing_det_stmt)).scalar_one_or_none()

            if existing_detection:
                existing_detection.occurrence_count += 1
                existing_detection.last_seen_at = now
                existing_detection.details_json = {
                    **(existing_detection.details_json or {}),
                    **sanitized_details,
                    "last_occurrence_count": existing_detection.occurrence_count,
                }
                triggered_detection = existing_detection
            else:
                # Create new normalized detection
                new_detection = SecurityDetection(
                    tenant_id=event.tenant_id,
                    rule_id=rule.rule_id,
                    rule_version=rule.version,
                    event_type=event.event_type,
                    severity=severity,
                    confidence=rule.confidence,
                    detection_source=event.detection_source,
                    actor_type=event.actor_type,
                    actor_id=event.actor_id,
                    target_resource_type=event.target_resource_type,
                    target_resource_id=event.target_resource_id,
                    ip_address=event.ip_address,
                    request_id=event.request_id,
                    audit_log_id=event.audit_log_id,
                    dedup_fingerprint=fingerprint,
                    occurrence_count=count,
                    first_seen_at=now,
                    last_seen_at=now,
                    details_json=sanitized_details,
                    status="UNTRIAGED",
                )
                db.add(new_detection)
                await db.flush()
                triggered_detection = new_detection

            # Group or link to an Incident if severity is HIGH or CRITICAL
            if severity in ("HIGH", "CRITICAL") and triggered_detection:
                await self._link_or_create_incident(
                    db=db,
                    detection=triggered_detection,
                    rule=rule,
                    event=event,
                )

        return triggered_detection

    async def _link_or_create_incident(
        self,
        db: AsyncSession,
        detection: SecurityDetection,
        rule: ThreatDetectionRule,
        event: NormalizedSecurityEvent,
    ) -> SecurityIncident:
        """Group detection into an active incident or create a new incident."""
        now = datetime.now(UTC)

        # Check if an existing open incident exists for this tenant and rule or fingerprint
        stmt = (
            select(SecurityIncident)
            .where(
                and_(
                    SecurityIncident.tenant_id == detection.tenant_id,
                    SecurityIncident.status.in_(["NEW", "TRIAGED", "INVESTIGATING", "CONTAINED", "REMEDIATING"]),
                )
            )
            .order_by(SecurityIncident.created_at.desc())
            .limit(10)
        )
        recent_incidents = (await db.execute(stmt)).scalars().all()

        matching_incident: SecurityIncident | None = None
        for inc in recent_incidents:
            # Check metadata or title similarity
            if inc.title == f"Security Alert: {rule.name}" or (inc.metadata_json and inc.metadata_json.get("rule_id") == rule.rule_id):
                matching_incident = inc
                break

        if matching_incident:
            detection.incident_id = matching_incident.id
            detection.status = "LINKED_TO_INCIDENT"
            # Upgrade severity if higher
            if rule.severity == "CRITICAL" and matching_incident.severity != "CRITICAL":
                matching_incident.severity = "CRITICAL"
            return matching_incident

        # Create new incident
        incident_number = await self._get_next_incident_number(db)
        title = f"Security Alert: {rule.name}"
        desc = (
            f"Automated threat detection alert triggered by {rule.rule_id} ({rule.name}).\n\n"
            f"**Event Type:** `{detection.event_type}`\n"
            f"**Source:** `{detection.detection_source}`\n"
            f"**Actor:** `{detection.actor_type}:{detection.actor_id or 'unknown'}`\n"
            f"**IP Address:** `{detection.ip_address}`\n"
            f"**Rule Rationale:** {rule.description}"
        )

        incident = SecurityIncident(
            tenant_id=detection.tenant_id,
            incident_number=incident_number,
            title=title,
            description=desc,
            severity=rule.severity,
            confidence=rule.confidence,
            status="NEW",
            metadata_json={
                "rule_id": rule.rule_id,
                "detection_source": detection.detection_source,
                "initial_ip": detection.ip_address,
            },
        )
        db.add(incident)
        await db.flush()

        detection.incident_id = incident.id
        detection.status = "LINKED_TO_INCIDENT"

        # Add initial timeline note
        initial_note = SecurityIncidentNote(
            incident_id=incident.id,
            author_user_id=None,
            note_type="TIMELINE",
            content=f"Incident opened automatically by Threat Detection Engine rule {rule.rule_id}.",
            evidence_references=[
                {
                    "detection_id": str(detection.id),
                    "rule_id": rule.rule_id,
                    "ip_address": detection.ip_address,
                    "audit_log_id": str(detection.audit_log_id) if detection.audit_log_id else None,
                }
            ],
        )
        db.add(initial_note)

        # Propose recommended containment action if defined
        if rule.recommended_action:
            requires_approval = rule.severity in ("CRITICAL", "HIGH")
            action = SecurityResponseAction(
                tenant_id=detection.tenant_id,
                incident_id=incident.id,
                action_type=rule.recommended_action,
                target_type="IP" if "IP" in rule.recommended_action else "SESSION",
                target_identifier=detection.ip_address if "IP" in rule.recommended_action else (detection.actor_id or "unknown"),
                risk_level=rule.severity,
                requires_approval=requires_approval,
                status="PROPOSED",
                idempotency_key=f"PROPOSE-{incident.incident_number}-{rule.recommended_action}-{uuid4().hex[:8]}",
                execution_payload={
                    "rule_id": rule.rule_id,
                    "incident_number": incident.incident_number,
                    "reason": f"Automatic response proposed by {rule.rule_id}",
                },
            )
            db.add(action)
            await db.flush()

        return incident

    def clear(self) -> None:
        """Clear memory buffers (used in test fixtures)."""
        self._sliding_windows.clear()
        self._ip_targeted_accounts.clear()


threat_engine = ThreatDetectionEngine()
