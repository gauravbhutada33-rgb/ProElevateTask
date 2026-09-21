import React, { useEffect, useState } from "react";

export type HITLProposalStatus =
  | "PENDING"
  | "CONFIRMING"
  | "CONFIRMED"
  | "QUEUED_RETRY"
  | "REJECTED"
  | "EXPIRED";

export interface HITLConfirmationCardProps {
  proposalId: string;
  employeeId: string;
  startDate: string;
  endDate: string;
  days: number;
  leaveType: string;
  remainingBalance: number;
  ttlSeconds?: number;
  initialStatus?: HITLProposalStatus;
  onDecisionCompleted?: (result: {
    proposal_id: string;
    status: HITLProposalStatus;
    workweek_transaction_id?: string;
    queue_name?: string;
  }) => void;
}

function formatCountdown(secondsLeft: number): string {
  const clamped = Math.max(0, secondsLeft);
  const mins = Math.floor(clamped / 60);
  const secs = clamped % 60;
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

export const HITLConfirmationCard: React.FC<HITLConfirmationCardProps> = ({
  proposalId,
  employeeId,
  startDate,
  endDate,
  days,
  leaveType,
  remainingBalance,
  ttlSeconds = 900,
  initialStatus = "PENDING",
  onDecisionCompleted,
}) => {
  const [status, setStatus] = useState<HITLProposalStatus>(initialStatus);
  const [secondsRemaining, setSecondsRemaining] = useState<number>(ttlSeconds);
  const [transactionId, setTransactionId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (status !== "PENDING") {
      return;
    }
    const interval = window.setInterval(() => {
      setSecondsRemaining((prev) => {
        if (prev <= 1) {
          setStatus("EXPIRED");
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => window.clearInterval(interval);
  }, [status]);

  const handleAction = async (decision: "CONFIRM" | "CANCEL") => {
    if (status !== "PENDING" || secondsRemaining <= 0) {
      return;
    }
    // Optimistic state locking to prevent double submission
    setStatus("CONFIRMING");
    setErrorMessage(null);

    try {
      const response = await fetch("/api/v1/hitl/confirm", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-employee-sub": employeeId,
        },
        body: JSON.stringify({
          proposal_id: proposalId,
          employee_id: employeeId,
          decision,
        }),
      });

      if (!response.ok) {
        if (response.status === 410) {
          setStatus("EXPIRED");
          return;
        }
        throw new Error(`HTTP ${response.status}: Failed to process HITL confirmation`);
      }

      const data = await response.json();
      const nextStatus: HITLProposalStatus = data.status || (decision === "CONFIRM" ? "CONFIRMED" : "REJECTED");
      setStatus(nextStatus);
      if (data.workweek_transaction_id) {
        setTransactionId(data.workweek_transaction_id);
      }
      onDecisionCompleted?.(data);
    } catch (err) {
      setStatus("PENDING");
      setErrorMessage(err instanceof Error ? err.message : "Network error while confirming leave request");
    }
  };

  const isLocked = status !== "PENDING" || secondsRemaining <= 0;

  return (
    <div
      className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
      data-testid="hitl-confirmation-card"
    >
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-indigo-600">
            WorkWeek HRIS • Two-Phase HITL Gate
          </span>
          <h3 className="text-base font-bold text-slate-900">
            Confirm {leaveType} Request ({proposalId})
          </h3>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-mono font-semibold ${
            secondsRemaining <= 60 || status === "EXPIRED"
              ? "bg-red-100 text-red-700"
              : "bg-amber-100 text-amber-800"
          }`}
          data-testid="hitl-countdown-badge"
        >
          TTL {formatCountdown(secondsRemaining)}
        </span>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <div className="rounded-lg bg-slate-50 p-2.5">
          <dt className="text-xs text-slate-500">Start Date</dt>
          <dd className="font-semibold text-slate-900">{startDate}</dd>
        </div>
        <div className="rounded-lg bg-slate-50 p-2.5">
          <dt className="text-xs text-slate-500">End Date</dt>
          <dd className="font-semibold text-slate-900">{endDate}</dd>
        </div>
        <div className="rounded-lg bg-slate-50 p-2.5">
          <dt className="text-xs text-slate-500">Duration</dt>
          <dd className="font-semibold text-slate-900">{days.toFixed(1)} Days</dd>
        </div>
        <div className="rounded-lg bg-slate-50 p-2.5">
          <dt className="text-xs text-slate-500">Remaining Balance</dt>
          <dd className="font-semibold text-emerald-700">{remainingBalance.toFixed(1)} Days</dd>
        </div>
      </dl>

      {errorMessage && (
        <p className="mt-3 text-xs font-medium text-red-600" role="alert">
          {errorMessage}
        </p>
      )}

      {transactionId && (
        <p className="mt-3 text-xs font-medium text-emerald-700">
          Submitted to WorkWeek HRIS • Transaction ID: <code className="font-mono">{transactionId}</code>
        </p>
      )}

      <div className="mt-4 flex items-center justify-end gap-3">
        <button
          type="button"
          disabled={isLocked}
          onClick={() => handleAction("CANCEL")}
          className="rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="button"
          disabled={isLocked}
          onClick={() => handleAction("CONFIRM")}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {status === "CONFIRMING"
            ? "Submitting..."
            : status === "CONFIRMED"
            ? "Confirmed in WorkWeek"
            : status === "QUEUED_RETRY"
            ? "Queued for Safe Retry"
            : "Confirm & Submit to WorkWeek"}
        </button>
      </div>
    </div>
  );
};

export default HITLConfirmationCard;
