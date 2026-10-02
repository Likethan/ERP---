"use client";

import React, { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  Award,
  ArrowLeft,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  MapPin,
  Briefcase,
  DollarSign,
  AlertTriangle,
  User,
  History,
  Printer,
  ChevronRight,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { placementService } from "@/services/placement.service";
import { formatLPA } from "@/services/placement-calculator";
import { Offer, OfferStatus } from "@/types/placement";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function OfferDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const { showToast } = useToast();

  const [offer, setOffer] = useState<Offer | null>(null);
  const [loading, setLoading] = useState(true);

  // Modals
  const [showAcceptModal, setShowAcceptModal] = useState(false);
  const [showDeclineModal, setShowDeclineModal] = useState(false);
  const [studentNotes, setStudentNotes] = useState("");
  const [declineReason, setDeclineReason] = useState("");
  const [processing, setProcessing] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await placementService.getOfferById(id);
      if (res.success && res.data) {
        setOffer(res.data);
      } else {
        showToast({
          title: "Offer Not Found",
          message: `Could not locate offer with identifier ${id}`,
          type: "error",
        });
      }
    } catch {
      showToast({
        title: "Network Error",
        message: "Failed to fetch corporate offer dossier",
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [id]);

  const handleAccept = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!offer) return;

    try {
      setProcessing(true);
      const res = await placementService.acceptOffer(offer.id, studentNotes);
      if (res.success) {
        showToast({
          title: "Offer Accepted!",
          message: `Congratulations! Offer from ${offer.companyName} accepted and placement confirmed.`,
          type: "success",
        });
        setShowAcceptModal(false);
        await loadData();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to accept offer";
      showToast({
        title: "Action Failed",
        message: msg,
        type: "error",
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleDecline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!offer) return;
    if (!declineReason.trim()) {
      showToast({
        title: "Validation Error",
        message: "Please state a reason for declining this offer",
        type: "error",
      });
      return;
    }

    try {
      setProcessing(true);
      const res = await placementService.declineOffer(offer.id, declineReason);
      if (res.success) {
        showToast({
          title: "Offer Declined",
          message: `Offer from ${offer.companyName} marked as declined.`,
          type: "info",
        });
        setShowDeclineModal(false);
        await loadData();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to decline offer";
      showToast({
        title: "Action Failed",
        message: msg,
        type: "error",
      });
    } finally {
      setProcessing(false);
    }
  };

  const getStatusBadge = (status: OfferStatus) => {
    switch (status) {
      case "ACCEPTED":
        return (
          <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 gap-1 text-sm py-1 px-3">
            <CheckCircle2 className="w-4 h-4" />
            Offer Accepted
          </Badge>
        );
      case "RELEASED":
        return (
          <Badge className="bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30 gap-1 text-sm py-1 px-3">
            <Clock className="w-4 h-4" />
            Offer Released (Awaiting Response)
          </Badge>
        );
      case "DECLINED":
        return (
          <Badge className="bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30 gap-1 text-sm py-1 px-3">
            <XCircle className="w-4 h-4" />
            Offer Declined
          </Badge>
        );
      case "DRAFT":
        return (
          <Badge className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30 gap-1 text-sm py-1 px-3">
            Draft
          </Badge>
        );
      case "EXPIRED":
        return (
          <Badge className="bg-slate-500/15 text-slate-600 dark:text-slate-400 border-slate-500/30 gap-1 text-sm py-1 px-3">
            <AlertTriangle className="w-4 h-4" />
            Expired
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-muted-foreground">Loading offer dossier...</p>
        </div>
      </div>
    );
  }

  if (!offer) {
    return (
      <div className="p-8 max-w-4xl mx-auto space-y-4">
        <Link href="/app/placement/offers">
          <Button variant="ghost" size="sm" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Offers
          </Button>
        </Link>
        <div className="bg-card border rounded-xl p-12 text-center space-y-3 shadow-sm">
          <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto" />
          <h2 className="text-lg font-bold text-foreground">Offer Not Found</h2>
          <p className="text-sm text-muted-foreground">
            The requested offer record could not be found or has been revoked.
          </p>
        </div>
      </div>
    );
  }

  const isExpired =
    offer.status === "RELEASED" && new Date(offer.responseDeadline).getTime() < Date.now();

  return (
    <div className="p-6 space-y-6 max-w-[1400px] mx-auto">
      {/* Back button */}
      <div>
        <Link href="/app/placement/offers">
          <Button variant="ghost" size="sm" className="gap-2 text-xs">
            <ArrowLeft className="w-4 h-4" />
            Back to Offers Ledger
          </Button>
        </Link>
      </div>

      {/* Top Banner if Accepted */}
      {offer.status === "ACCEPTED" && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-semibold text-emerald-800 dark:text-emerald-300 text-sm">
                Offer Officially Accepted
              </h3>
              <p className="text-xs text-emerald-700/80 dark:text-emerald-400/80">
                Placement confirmed for {offer.studentName} at {offer.companyName}. Record automatically reflected in CampusOS Placement Outcomes.
              </p>
            </div>
          </div>
          <Link href="/app/placement/outcomes">
            <Button size="sm" variant="outline" className="border-emerald-500/30 text-emerald-700 dark:text-emerald-300 gap-1 text-xs">
              View Outcomes Ledger
              <ChevronRight className="w-3.5 h-3.5" />
            </Button>
          </Link>
        </div>
      )}

      {/* Main Header Dossier */}
      <div className="bg-card border rounded-xl p-6 shadow-sm flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground font-mono">
              {offer.offerCode}
            </h1>
            {getStatusBadge(offer.status)}
            <Badge variant="outline" className="text-xs">
              {offer.employmentType.replace(/_/g, " ")}
            </Badge>
          </div>

          <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-sm text-muted-foreground">
            <Link
              href={`/app/placement/students/${offer.studentId}`}
              className="flex items-center gap-1.5 text-foreground hover:text-primary font-medium"
            >
              <User className="w-4 h-4 text-primary" />
              {offer.studentName} ({offer.rollNumber})
            </Link>
            <span className="text-border">•</span>
            <Link
              href={`/app/placement/companies/${offer.companyId}`}
              className="flex items-center gap-1.5 text-foreground hover:text-primary font-medium"
            >
              <Building2 className="w-4 h-4 text-primary" />
              {offer.companyName}
            </Link>
            <span className="text-border">•</span>
            <span className="flex items-center gap-1.5">
              <Briefcase className="w-4 h-4 text-muted-foreground" />
              {offer.positionTitle}
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {offer.status === "RELEASED" && !isExpired && (
            <>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setShowDeclineModal(true)}
                className="gap-1.5 text-xs"
              >
                <XCircle className="w-3.5 h-3.5" />
                Decline Offer
              </Button>
              <Button
                size="sm"
                onClick={() => setShowAcceptModal(true)}
                className="bg-emerald-600 hover:bg-emerald-700 text-white gap-1.5 text-xs shadow-sm"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Accept Offer
              </Button>
            </>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={() => window.print()}
            className="gap-1.5 text-xs"
          >
            <Printer className="w-3.5 h-3.5" />
            Print Dossier
          </Button>
        </div>
      </div>

      {/* Grid Layout: Compensation Details & Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: CTC Card & Breakdown */}
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-base flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-emerald-500" />
                  Compensation & CTC Breakdown
                </span>
                <span className="text-xs text-muted-foreground font-normal">
                  Annualized Package Figures
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              {/* Grand Total Hero Box */}
              <div className="bg-gradient-to-br from-emerald-500/10 via-emerald-500/5 to-transparent border border-emerald-500/20 rounded-xl p-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                  <span className="text-xs uppercase tracking-wider font-semibold text-emerald-600 dark:text-emerald-400">
                    Total Cost to Company (CTC)
                  </span>
                  <div className="text-3xl font-extrabold text-foreground mt-0.5">
                    {formatLPA(offer.ctcLpa)}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Fixed Base + Performance Incentive + Comprehensive Corporate Benefits
                  </p>
                </div>

                <div className="text-right sm:border-l sm:pl-6 border-emerald-500/20">
                  <span className="text-xs text-muted-foreground">Monthly Equivalent</span>
                  <div className="text-lg font-bold text-foreground">
                    ₹{Math.round((offer.ctcLpa * 100000) / 12).toLocaleString("en-IN")}/mo
                  </div>
                  <span className="text-[11px] text-muted-foreground">Gross Pre-Tax</span>
                </div>
              </div>

              {/* Breakdown Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-card border rounded-lg p-3.5 space-y-1">
                  <span className="text-xs text-muted-foreground">Base Salary (Fixed)</span>
                  <div className="text-lg font-bold text-foreground">
                    {formatLPA(offer.baseSalaryLpa)}
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    Guaranteed fixed compensation paid across 12 cycles
                  </p>
                </div>

                <div className="bg-card border rounded-lg p-3.5 space-y-1">
                  <span className="text-xs text-muted-foreground">Variable / Bonus</span>
                  <div className="text-lg font-bold text-foreground">
                    {offer.variableLpa ? formatLPA(offer.variableLpa) : "None"}
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    Performance linked annual incentive
                  </p>
                </div>

                <div className="bg-card border rounded-lg p-3.5 space-y-1">
                  <span className="text-xs text-muted-foreground">Internship Stipend</span>
                  <div className="text-lg font-bold text-foreground">
                    {offer.stipendMonthly ? `₹${offer.stipendMonthly.toLocaleString()}/mo` : "N/A"}
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    Applicable during pre-graduation training
                  </p>
                </div>
              </div>

              {/* Key Recruitment Terms */}
              <div className="border-t pt-4 space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Employment Logistics & Dates
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div className="flex items-center justify-between p-2.5 bg-muted/30 rounded-lg">
                    <span className="text-muted-foreground flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5" />
                      Posting Location
                    </span>
                    <span className="font-semibold text-foreground">{offer.location}</span>
                  </div>

                  <div className="flex items-center justify-between p-2.5 bg-muted/30 rounded-lg">
                    <span className="text-muted-foreground flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5" />
                      Joining Date
                    </span>
                    <span className="font-semibold text-foreground">{offer.joiningDate}</span>
                  </div>

                  <div className="flex items-center justify-between p-2.5 bg-muted/30 rounded-lg">
                    <span className="text-muted-foreground flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      Offer Issue Date
                    </span>
                    <span className="font-semibold text-foreground">{offer.offerDate}</span>
                  </div>

                  <div className="flex items-center justify-between p-2.5 bg-muted/30 rounded-lg">
                    <span className="text-muted-foreground flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                      Response Deadline
                    </span>
                    <span className="font-semibold text-foreground">{offer.responseDeadline}</span>
                  </div>
                </div>
              </div>

              {/* Response Notes / Candidate Feedback */}
              {offer.responseNotes && (
                <div className="border-t pt-4 space-y-2">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Candidate Response Record
                  </h4>
                  <div className="p-3 bg-muted/40 rounded-lg text-xs border space-y-1">
                    <span className="font-semibold text-foreground">
                      Notes recorded upon decision:
                    </span>
                    <p className="text-muted-foreground italic">&ldquo;{offer.responseNotes}&rdquo;</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Audit Timeline & Issuing Authority */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-base flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-primary" />
                Issuing Authority
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b">
                <span className="text-muted-foreground">Released By</span>
                <span className="font-semibold text-foreground">{offer.releasedBy}</span>
              </div>
              <div className="flex justify-between py-1 border-b">
                <span className="text-muted-foreground">Related Application</span>
                <Link
                  href={`/app/placement/applications/${offer.applicationId}`}
                  className="font-mono text-primary hover:underline"
                >
                  View Application
                </Link>
              </div>
              <div className="flex justify-between py-1 border-b">
                <span className="text-muted-foreground">Corporate Partner</span>
                <Link
                  href={`/app/placement/companies/${offer.companyId}`}
                  className="font-medium text-foreground hover:text-primary"
                >
                  {offer.companyName}
                </Link>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-muted-foreground">Candidate Profile</span>
                <Link
                  href={`/app/placement/students/${offer.studentId}`}
                  className="font-medium text-foreground hover:text-primary"
                >
                  {offer.studentName}
                </Link>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-base flex items-center gap-2">
                <History className="w-4 h-4 text-muted-foreground" />
                Offer Lifecycle Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-border">
                {offer.timeline && offer.timeline.length > 0 ? (
                  offer.timeline.map((event) => (
                    <div key={event.id} className="relative">
                      <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-primary border-2 border-background" />
                      <div className="space-y-0.5">
                        <div className="text-xs font-semibold text-foreground">
                          {event.action}
                        </div>
                        <div className="text-[11px] text-muted-foreground flex items-center gap-1.5">
                          <span>{event.actor}</span>
                          <span>•</span>
                          <span>{new Date(event.timestamp).toLocaleDateString()}</span>
                        </div>
                        {event.details && (
                          <p className="text-xs text-muted-foreground mt-1 bg-muted/30 p-2 rounded">
                            {event.details}
                          </p>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-muted-foreground">No events recorded.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Accept Offer Confirmation Modal */}
      {showAcceptModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="bg-card border rounded-xl shadow-2xl max-w-md w-full p-6 space-y-5">
            <div className="flex items-center justify-between border-b pb-3">
              <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                Accept Recruitment Offer
              </h2>
              <button
                onClick={() => setShowAcceptModal(false)}
                className="text-muted-foreground hover:text-foreground text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-3 text-xs space-y-1">
              <div className="font-semibold text-foreground">
                Confirm acceptance of corporate appointment:
              </div>
              <div className="text-muted-foreground">
                <strong>Company:</strong> {offer.companyName}
              </div>
              <div className="text-muted-foreground">
                <strong>Position:</strong> {offer.positionTitle}
              </div>
              <div className="text-muted-foreground">
                <strong>Compensation:</strong> {formatLPA(offer.ctcLpa)}
              </div>
            </div>

            <form onSubmit={handleAccept} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Acceptance Notes / Remarks (Optional)
                </label>
                <textarea
                  rows={3}
                  value={studentNotes}
                  onChange={(e) => setStudentNotes(e.target.value)}
                  placeholder="e.g. Delighted to accept. Thank you for the opportunity."
                  className="w-full text-xs p-2.5 rounded-lg border bg-background text-foreground"
                />
              </div>

              <p className="text-[11px] text-muted-foreground">
                By clicking <strong>Confirm Acceptance</strong>, you confirm your commitment to join {offer.companyName}.
                This will automatically update your CampusOS placement dossier to <strong>PLACED</strong>.
              </p>

              <div className="flex items-center justify-end gap-2 pt-2 border-t">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAcceptModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={processing}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  {processing ? "Processing..." : "Confirm Acceptance"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Decline Offer Modal */}
      {showDeclineModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="bg-card border rounded-xl shadow-2xl max-w-md w-full p-6 space-y-5">
            <div className="flex items-center justify-between border-b pb-3">
              <h2 className="text-base font-bold text-foreground flex items-center gap-2">
                <XCircle className="w-5 h-5 text-rose-500" />
                Decline Recruitment Offer
              </h2>
              <button
                onClick={() => setShowDeclineModal(false)}
                className="text-muted-foreground hover:text-foreground text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleDecline} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">
                  Reason for Declining <span className="text-destructive">*</span>
                </label>
                <textarea
                  rows={3}
                  required
                  value={declineReason}
                  onChange={(e) => setDeclineReason(e.target.value)}
                  placeholder="e.g. Opting for higher studies / accepted dream offer at alternative partner"
                  className="w-full text-xs p-2.5 rounded-lg border bg-background text-foreground"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowDeclineModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  variant="destructive"
                  disabled={processing}
                >
                  {processing ? "Processing..." : "Confirm Decline"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
