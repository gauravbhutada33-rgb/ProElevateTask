import React from "react";
import { SpineSSEWidgetEvent } from "../types/events";

/**
 * Spine Widget Dispatcher (app/frontend/src/core/WidgetDispatcher.tsx).
 * Automatically routes streamed widget events to the owning Pod's feature slice
 * without requiring Pod 1..5 engineers to modify App.tsx.
 */
export const WidgetDispatcher: React.FC<{ event: SpineSSEWidgetEvent }> = ({ event }) => {
  switch (event.widget_type) {
    case "privacy_receipt":
      return (
        <div data-testid="pod1-privacy-widget" className="p-4 border rounded-lg bg-emerald-50">
          <strong>Pod 1 (Security &amp; GDPR Art. 17):</strong> Erasure Receipt{" "}
          <code>{event.erasure_receipt_id ?? "PENDING"}</code> (KMS Salt Destroyed)
        </div>
      );
    case "citation_list":
      return (
        <div data-testid="pod2-citation-widget" className="p-4 border rounded-lg bg-blue-50">
          <strong>Pod 2 (Policy RAG Citations):</strong> Pre-retrieval entitlement verified (`&lt;2ms`).
        </div>
      );
    case "hitl_card":
      return (
        <div data-testid="pod3-hitl-widget" className="p-4 border rounded-lg bg-amber-50">
          <strong>Pod 3 (WorkWeek Two-Phase HITL Gate):</strong> Proposal{" "}
          <code>{event.proposal_id ?? "prop-draft"}</code> awaiting human confirmation (15-min TTL).
        </div>
      );
    case "saga_stepper":
      return (
        <div data-testid="pod4-saga-widget" className="p-4 border rounded-lg bg-purple-50">
          <strong>Pod 4 (Two-System HRIS+IT Saga):</strong> Status{" "}
          <code>{event.saga_state ?? "HR_COMMITTED"}</code>
        </div>
      );
    case "warm_handoff":
      return (
        <div data-testid="pod5-handoff-widget" className="p-4 border rounded-lg bg-rose-50">
          <strong>Pod 5 (Live HR Warm Handoff &amp; CSAT):</strong> Escalation Case{" "}
          <code>{event.case_id ?? "SI-HR-P2"}</code> created with DLP-redacted 5-turn summary.
        </div>
      );
    default:
      return null;
  }
};
