/**
 * Shared Spine SSE & Widget Contracts (app/frontend/src/types/events.ts).
 * All 5 Pods emit one of these typed widget payloads over `/api/v1/chat/stream`.
 */

export type PodWidgetType =
  | "privacy_receipt"   // Pod 1: GDPR Art. 17 Crypto-Shredding Receipt & PII Redaction Banner
  | "citation_list"     // Pod 2: Policy RAG Inline Citations & Source Drawer
  | "hitl_card"         // Pod 3: Two-Phase WorkWeek Leave Confirmation Card (15-min TTL)
  | "saga_stepper"      // Pod 4: Two-System (WorkWeek + ServiceImmediately) Saga Progress & Rollback
  | "warm_handoff";     // Pod 5: Distressed Employee Live P2 HR Case Handoff & CSAT Survey

export interface SpineSSEWidgetEvent {
  type: "widget";
  widget_type: PodWidgetType;
  employee_id: string;
  proposal_id?: string;
  erasure_receipt_id?: string;
  citations?: Array<{ doc_id: string; section_anchor: string; snippet: string }>;
  saga_state?: "HR_COMMITTED" | "COMPLETED" | "ROLLBACK_EXECUTED";
  case_id?: string;
  timestamp_utc: string;
}
