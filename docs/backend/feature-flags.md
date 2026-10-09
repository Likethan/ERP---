# Feature Flag System

The **Feature Flag System** enables progressive delivery, controlled beta rollouts, and runtime feature toggling without redeployments.

---

## 1. Architectural Principles

- **Authoritative Backend Enforcement**: Feature flags are evaluated server-side. Frontend flags are strictly presentation hints; backend authorization and API guards remain authoritative.
- **Multi-Tenant Scoping**: Feature flags support:
  - `PLATFORM`: Platform-wide enablement.
  - `TENANT`: University-specific feature access (e.g. enabling AI Assistant for an enterprise campus).
- **Safe Rollout Percentages**: Canary rollouts use deterministic SHA-256 bucketing:
  $$\text{hash} = \text{SHA256}(\text{key} + \text{user\_id}) \pmod{100}$$
  Ensures a given user consistently experiences the same variant across sessions.
- **Environment Targeting**: Flags can be restricted to specific environments (e.g. `development`, `staging`, `production`).
- **User & Role Targeting**: Flags can target specific user IDs or RBAC roles (e.g., `DEAN`, `FACULTY`).
- **Time Bounds**: Optional `starts_at` and `expires_at` parameters automate activation and decommissioning.

---

## 2. Feature Flag Entity Structure

```python
class FeatureFlag(BaseModel):
    id: UUID
    key: str  # e.g. "intelligence.ai_assistant"
    name: str
    description: Optional[str]
    tenant_id: Optional[UUID]  # None for platform-level flags
    module: Optional[str]      # e.g. "INTELLIGENCE", "FINANCE"
    is_enabled: bool
    rollout_percentage: int     # 0 to 100
    target_environments: List[str] # ["development", "staging", "production"]
    target_roles: List[str]    # ["SUPER_ADMIN", "INSTITUTION_ADMIN"]
    target_users: List[UUID]   # List of user UUIDs
    starts_at: Optional[datetime]
    expires_at: Optional[datetime]
```

---

## 3. Evaluation Resolution

Evaluation executes in the following sequence:

1. **Existence & State**: If flag does not exist or `is_enabled == False`, returns `False`.
2. **Time Window**: If `now < starts_at` or `now > expires_at`, returns `False`.
3. **Environment**: If `target_environments` is non-empty and current environment is not listed, returns `False`.
4. **User Target**: If `user_id` matches `target_users`, returns `True` immediately.
5. **Role Target**: If `user_role` matches `target_roles`, returns `True` immediately.
6. **Rollout Percentage**: If `rollout_percentage < 100`, calculates deterministic hash bucket. If bucket $\ge \text{rollout\_percentage}$, returns `False`.
7. **Default**: Returns `True`.

---

## 4. Usage Example

```python
from app.services.feature_flag_service import FeatureFlagService

flag_service = FeatureFlagService(db_session)
is_active = await flag_service.is_enabled(
    key="intelligence.ai_assistant",
    tenant_id=tenant_id,
    user_id=current_user.id,
    user_role=current_user.role,
    environment="production"
)

if not is_active:
    raise FeatureDisabledException("AI Assistant is not enabled for this institution.")
```
