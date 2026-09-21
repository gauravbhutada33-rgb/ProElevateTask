import React, { useState } from "react";
import { SpineSSEWidgetEvent } from "../types/events";

/**
 * v2 Intuitive Spine Widget Dispatcher (app/frontend/src/core/WidgetDispatcher.tsx).
 * Implements the Progressive-Disclosure & 'Less, but better' v2 Design Language
 * across all 5 Pod widgets with zero SDD deviation.
 */
export const WidgetDispatcher: React.FC<{
  event: SpineSSEWidgetEvent;
  onConfirmProposal?: (proposalId: string, decision: "CONFIRM" | "CANCEL") => void;
}> = ({ event, onConfirmProposal }) => {
  const [status, setStatus] = useState<"PENDING" | "CONFIRMED" | "CANCELLED">("PENDING");

  const handleDecision = (decision: "CONFIRM" | "CANCEL") => {
    setStatus(decision === "CONFIRM" ? "CONFIRMED" : "CANCELLED");
    if (onConfirmProposal && event.proposal_id) {
      onConfirmProposal(event.proposal_id, decision);
    }
  };

  switch (event.widget_type) {
    case "privacy_receipt":
      return (
        <div
          data-testid="pod1-privacy-widget"
          className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-4 space-y-2"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-700">
              ✓ GDPR Article 17 Cryptographic Erasure Complete
            </span>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-700">
              {event.erasure_receipt_id ?? "ERASURE-9F4A2C"}
            </span>
          </div>
          <p className="text-xs text-slate-600">
            Per-user KMS cryptographic salt destroyed (`user_salts` purged). Immutable 7-year
            compliance ledger preserved with zero raw PII.
          </p>
        </div>
      );

    case "citation_list":
      return (
        <div
          data-testid="pod2-citation-widget"
          className="rounded-2xl border border-blue-500/20 bg-blue-500/5 p-3.5 flex items-center justify-between"
        >
          <div className="space-y-0.5">
            <div className="text-xs font-semibold text-blue-700">
              SG Leave Policy §3.1 (`DOC-SG-LEAVE-2026#sec-3.1`)
            </div>
            <p className="text-[11px] text-slate-600">
              Entitlement Verified (`&lt;2ms` SQL Pre-Filter: Singapore / IC)
            </p>
          </div>
          <span className="text-xs font-medium text-blue-600">View in Source Inspector →</span>
        </div>
      );

    case "hitl_card":
      return (
        <div
          data-testid="pod3-hitl-widget"
          className="rounded-2xl border-2 border-amber-500/40 bg-white p-4 space-y-3.5 shadow-sm"
        >
          <div className="flex items-center justify-between">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/15 text-amber-700">
              {status === "PENDING"
                ? "Awaiting Your Confirmation • Expires in 14:52"
                : status === "CONFIRMED"
                  ? "✓ Confirmed & Sent to WorkWeek"
                  : "✕ Request Cancelled"}
            </span>
            <span className="text-[11px] font-mono text-slate-500">
              ID: {event.proposal_id ?? "prop-8841"}
            </span>
          </div>

          {/* Visual Balance-Delta Bar */}
          <div className="space-y-1.5 bg-slate-50 p-3 rounded-xl border border-slate-200">
            <div className="flex justify-between text-xs font-medium text-slate-700">
              <span>Balance delta (Annual Vacation)</span>
              <span className="text-emerald-700 font-semibold">
                15.0d current → 3.0d requested → 12.0d remaining
              </span>
            </div>
            <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden flex">
              <div className="bg-emerald-600 h-full" style={{ width: "60%" }} />
              <div
                className="bg-amber-400 h-full transition-all"
                style={{ width: status === "CANCELLED" ? "0%" : "15%" }}
              />
            </div>
          </div>

          {status === "PENDING" && (
            <div className="flex items-center justify-between pt-1">
              <span className="text-[11px] text-slate-500">
                🔒 Protected by Two-Phase Approval Gate (`POST /api/v1/hitl/confirm`)
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleDecision("CANCEL")}
                  className="px-3.5 py-2 rounded-xl border border-slate-200 text-xs font-medium hover:bg-slate-50"
                >
                  Edit / Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleDecision("CONFIRM")}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm"
                >
                  Confirm &amp; Send to WorkWeek
                </button>
              </div>
            </div>
          )}
        </div>
      );

    case "saga_stepper":
      return (
        <div
          data-testid="pod4-saga-widget"
          className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm"
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-700">
              Self-Healing Request Tracker • Zero Data Drift
            </span>
            <span className="text-[11px] font-mono text-slate-500">
              State: {event.saga_state ?? "ROLLBACK_EXECUTED"}
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
              <div className="font-semibold text-emerald-700">Step 1 • WorkWeek</div>
              <div className="text-[11px] text-slate-600">Address Drafted (`WW-TX-501`)</div>
            </div>
            <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200">
              <div className="font-semibold text-amber-700">Step 2 • IT Desk Busy</div>
              <div className="text-[11px] text-slate-600">Temporary Outage (`HTTP 503`)</div>
            </div>
            <div className="p-2.5 rounded-xl bg-indigo-50 border border-indigo-200">
              <div className="font-semibold text-indigo-700">Step 3 • Safely Reverted</div>
              <div className="text-[11px] text-slate-600">
                Restored &amp; Auto-Scheduled (`#TASK-RETRY-77`)
              </div>
            </div>
          </div>
        </div>
      );

    case "warm_handoff":
      return (
        <div
          data-testid="pod5-handoff-widget"
          className="rounded-2xl border border-rose-500/30 bg-white p-4 space-y-2.5 shadow-sm"
        >
          <div className="flex items-center justify-between">
            <div className="text-xs font-semibold text-slate-800">
              Connected to HR Specialist • Priority Case {event.case_id ?? "SI-HR-40912"}
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded bg-rose-500/10 text-rose-700 font-medium">
              Estimated reply &lt; 2 hrs
            </span>
          </div>
          <p className="text-xs text-slate-600">
            A privacy-redacted 5-turn summary has been shared with your People Partner so you won’t
            need to repeat yourself.
          </p>
        </div>
      );

    default:
      return null;
  }
};
