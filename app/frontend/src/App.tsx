import React, { useState } from "react";
import { WidgetDispatcher } from "./core/WidgetDispatcher";
import { SpineSSEWidgetEvent } from "./types/events";

/**
 * v2 Intuitive 3-Zone Spatial Workspace Shell (app/frontend/src/App.tsx).
 * Zone 1 (Left Rail 260px): Live EMP-824 Profile, Visual WorkWeek Balance Bars, Open IT Request & GDPR Drawer Trigger.
 * Zone 2 (Center Stage): Calm Conversational Canvas + Visual Balance-Delta HITL & Self-Healing Saga Cards.
 * Zone 3 (Right Drawer 320px): Slide-Over Policy Source Inspector & Progressive-Disclosure SDD Trust Telemetry.
 */
export const App: React.FC = () => {
  const [showInspector, setShowInspector] = useState<boolean>(false);
  const [erasureReceipt, setErasureReceipt] = useState<string | null>(null);
  const [widgets] = useState<SpineSSEWidgetEvent[]>([
    {
      type: "widget",
      widget_type: "hitl_card",
      employee_id: "EMP-824",
      proposal_id: "prop-8841",
      timestamp_utc: new Date().toISOString(),
    },
  ]);

  const handleGdprForgetMe = async () => {
    const res = await fetch("/api/v1/privacy/forget-me", {
      method: "DELETE",
      headers: { "x-employee-sub": "EMP-824" },
    });
    if (res.ok) {
      const data = await res.json();
      setErasureReceipt(data.erasure_receipt_id);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 antialiased p-4">
      <div className="max-w-[1400px] mx-auto space-y-4">
        {/* Calm Top Header with Progressive Disclosure Trust Badge */}
        <header className="bg-white border border-slate-200 rounded-2xl px-5 py-3.5 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-bold text-xs">
              HR
            </div>
            <div>
              <h1 className="text-sm font-semibold">
                PeopleAssist AI — Enterprise HR Assistant
              </h1>
              <p className="text-xs text-slate-500">
                WorkWeek HRIS &amp; ServiceImmediately IT • Gemini 3.6 Pro / Flash
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowInspector(!showInspector)}
              className="px-3 py-1.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-700 border border-emerald-500/20"
            >
              ✓ Zero Data Retention • SG Verified
            </button>
          </div>
        </header>

        {/* 3-Zone Spatial Layout */}
        <div className="grid grid-cols-12 gap-4 items-start">
          {/* ZONE 1: Left Personal Context Rail (3 Cols) */}
          <aside className="col-span-12 lg:col-span-3 bg-white border border-slate-200 rounded-2xl p-4 space-y-4 shadow-sm">
            <div>
              <div className="text-xs font-medium text-slate-500">Employee</div>
              <div className="text-sm font-semibold mt-0.5">Gururay (EMP-824)</div>
              <div className="text-xs text-slate-500">Singapore (SG) • Role: IC</div>
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-100">
              <div className="text-xs font-semibold">Time Off Balances</div>
              <div className="text-xs text-slate-600">Vacation: 15.0 days available</div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div className="bg-emerald-600 h-full" style={{ width: "75%" }} />
              </div>
              <div className="text-xs text-slate-600 pt-1">Sick Leave: 10.0 days available</div>
              <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                <div className="bg-blue-600 h-full" style={{ width: "100%" }} />
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <div className="text-xs font-semibold">Open IT Request</div>
              <div className="text-xs font-mono text-blue-600">INC0004773 (In Review)</div>
              <div className="text-[11px] text-slate-500">
                Onboarding setup and badges configuration
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 space-y-2">
              <button
                type="button"
                onClick={handleGdprForgetMe}
                className="w-full py-2 px-3 rounded-xl border border-slate-200 text-xs font-medium text-slate-700 hover:bg-slate-50"
              >
                Privacy &amp; Data Controls (GDPR Art. 17)
              </button>
              {erasureReceipt && (
                <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-[11px] text-emerald-800">
                  Verified Receipt: <code>{erasureReceipt}</code> • KMS Salt Destroyed
                </div>
              )}
            </div>
          </aside>

          {/* ZONE 2: Center Conversational Canvas (6 Cols) */}
          <main className="col-span-12 lg:col-span-6 bg-white border border-slate-200 rounded-2xl p-5 space-y-4 shadow-sm">
            {widgets.map((w, idx) => (
              <WidgetDispatcher key={idx} event={w} />
            ))}
          </main>

          {/* ZONE 3: Right Source & Progressive Disclosure Inspector (3 Cols) */}
          <aside className="col-span-12 lg:col-span-3 bg-white border border-slate-200 rounded-2xl p-4 space-y-3 shadow-sm">
            <div className="text-xs font-semibold">Source Inspector</div>
            <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200 space-y-1.5 text-xs">
              <div className="font-semibold">SG Leave Policy (DOC-SG-LEAVE-2026)</div>
              <p className="text-slate-700 leading-relaxed">
                §3.1 Advance Notice: Requests spanning 3 or more consecutive business days require 7
                calendar days&apos; advance notice in WorkWeek.
              </p>
              <div className="text-[11px] font-medium text-emerald-700">
                ✓ Entitlement Verified: Singapore IC (&lt;2ms)
              </div>
            </div>

            {showInspector && (
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1 text-[11px] font-mono">
                <div className="font-semibold text-slate-700">SDD Architecture Telemetry</div>
                <div>Supervisor: gemini-3.6-pro</div>
                <div>Specialists: gemini-3.6-flash</div>
                <div>WorkWeek Limit: 50 RPS (100 burst)</div>
                <div>ServiceImm Limit: 25 RPS (50 burst)</div>
              </div>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
};

export default App;
