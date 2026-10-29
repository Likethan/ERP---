import React from "react";
import { Badge } from "@/components/ui/badge";
import {
  InsightPriority,
  InsightStatus,
  AlertSeverity,
  AlertStatus,
  IntelligenceDomain,
} from "@campusos/types";
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  Clock,
  Sparkles,
  BookOpen,
  Calendar,
  IndianRupee,
  Briefcase,
  Building,
  FileText,
  Users,
} from "lucide-react";

export function PriorityBadge({
  priority,
}: {
  priority: InsightPriority | string;
}) {
  switch (priority) {
    case InsightPriority.CRITICAL:
    case "CRITICAL":
      return (
        <Badge variant="danger" className="gap-1 font-semibold">
          <AlertCircle className="w-3 h-3" /> Critical
        </Badge>
      );
    case InsightPriority.HIGH:
    case "HIGH":
      return (
        <Badge
          variant="warning"
          className="gap-1 font-semibold text-amber-700 bg-amber-50 border-amber-200"
        >
          <AlertTriangle className="w-3 h-3" /> High Priority
        </Badge>
      );
    case InsightPriority.MEDIUM:
    case "MEDIUM":
      return (
        <Badge
          variant="neutral"
          className="gap-1 text-slate-700 bg-slate-100 border-slate-200"
        >
          <Clock className="w-3 h-3" /> Medium
        </Badge>
      );
    case InsightPriority.LOW:
    case "LOW":
      return (
        <Badge
          variant="neutral"
          className="gap-1 text-slate-600 bg-slate-50 border-slate-200"
        >
          Low
        </Badge>
      );
    default:
      return (
        <Badge variant="info" className="gap-1">
          <Info className="w-3 h-3" /> Info
        </Badge>
      );
  }
}

export function SeverityBadge({
  severity,
}: {
  severity: AlertSeverity | string;
}) {
  switch (severity) {
    case AlertSeverity.CRITICAL:
    case "CRITICAL":
      return (
        <Badge variant="danger" className="gap-1 font-semibold animate-pulse">
          <AlertCircle className="w-3 h-3" /> Critical
        </Badge>
      );
    case AlertSeverity.HIGH:
    case "HIGH":
      return (
        <Badge
          variant="warning"
          className="gap-1 font-semibold text-rose-700 bg-rose-50 border-rose-200"
        >
          <AlertTriangle className="w-3 h-3" /> High
        </Badge>
      );
    case AlertSeverity.WARNING:
    case "WARNING":
      return (
        <Badge
          variant="warning"
          className="gap-1 font-semibold text-amber-700 bg-amber-50 border-amber-200"
        >
          <AlertTriangle className="w-3 h-3" /> Warning
        </Badge>
      );
    default:
      return (
        <Badge variant="info" className="gap-1">
          <Info className="w-3 h-3" /> Info
        </Badge>
      );
  }
}

export function InsightStatusBadge({
  status,
}: {
  status: InsightStatus | string;
}) {
  switch (status) {
    case InsightStatus.NEW:
    case "NEW":
      return (
        <Badge
          variant="info"
          className="gap-1 font-medium bg-blue-50 text-blue-700 border-blue-200"
        >
          <Sparkles className="w-3 h-3" /> New
        </Badge>
      );
    case InsightStatus.REVIEWED:
    case "REVIEWED":
      return (
        <Badge
          variant="neutral"
          className="gap-1 text-slate-700 bg-slate-100 border-slate-200"
        >
          <Clock className="w-3 h-3" /> Reviewed
        </Badge>
      );
    case InsightStatus.ACTIONED:
    case "ACTIONED":
      return (
        <Badge
          variant="success"
          className="gap-1 font-medium bg-emerald-50 text-emerald-700 border-emerald-200"
        >
          <CheckCircle2 className="w-3 h-3" /> Actioned
        </Badge>
      );
    default:
      return (
        <Badge
          variant="neutral"
          className="text-slate-500 bg-slate-50 border-slate-200"
        >
          Dismissed
        </Badge>
      );
  }
}

export function AlertStatusBadge({ status }: { status: AlertStatus | string }) {
  switch (status) {
    case AlertStatus.OPEN:
    case "OPEN":
      return (
        <Badge variant="danger" className="gap-1 font-medium">
          Open
        </Badge>
      );
    case AlertStatus.ACKNOWLEDGED:
    case "ACKNOWLEDGED":
      return (
        <Badge
          variant="warning"
          className="gap-1 font-medium text-amber-700 bg-amber-50 border-amber-200"
        >
          Acknowledged
        </Badge>
      );
    case AlertStatus.RESOLVED:
    case "RESOLVED":
      return (
        <Badge
          variant="success"
          className="gap-1 font-medium bg-emerald-50 text-emerald-700 border-emerald-200"
        >
          Resolved
        </Badge>
      );
    default:
      return (
        <Badge
          variant="neutral"
          className="text-slate-500 bg-slate-50 border-slate-200"
        >
          Dismissed
        </Badge>
      );
  }
}

export function DomainBadge({
  domain,
}: {
  domain: IntelligenceDomain | string;
}) {
  const getDomainIcon = () => {
    switch (domain) {
      case IntelligenceDomain.ACADEMICS:
      case "ACADEMICS":
        return <BookOpen className="w-3 h-3" />;
      case IntelligenceDomain.ATTENDANCE:
      case "ATTENDANCE":
        return <Calendar className="w-3 h-3" />;
      case IntelligenceDomain.FINANCE:
      case "FINANCE":
        return <IndianRupee className="w-3 h-3" />;
      case IntelligenceDomain.PLACEMENT:
      case "PLACEMENT":
        return <Briefcase className="w-3 h-3" />;
      case IntelligenceDomain.INFRASTRUCTURE:
      case "INFRASTRUCTURE":
        return <Building className="w-3 h-3" />;
      case IntelligenceDomain.DOCUMENTS:
      case "DOCUMENTS":
        return <FileText className="w-3 h-3" />;
      case IntelligenceDomain.PEOPLE:
      case "PEOPLE":
        return <Users className="w-3 h-3" />;
      default:
        return <Sparkles className="w-3 h-3" />;
    }
  };

  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-800 border border-slate-200">
      {getDomainIcon()}
      {domain}
    </span>
  );
}
