import React, { useState } from "react";
import { WidgetDispatcher } from "./core/WidgetDispatcher";
import { SpineSSEWidgetEvent } from "./types/events";

/**
 * Main Spine Chat Application Shell (app/frontend/src/App.tsx).
 * Connects to `POST /api/v1/chat/stream` and `DELETE /api/v1/privacy/forget-me`.
 */
export const App: React.FC = () => {
  const [messages, setMessages] = useState<string[]>([]);
  const [widgets, setWidgets] = useState<SpineSSEWidgetEvent[]>([]);

  return (
    <main className="max-w-4xl mx-auto p-6 space-y-4">
      <header className="flex items-center justify-between border-b pb-4">
        <div>
          <h1 className="text-xl font-bold">Enterprise HR Agentic Assistant (MVP 1)</h1>
          <p className="text-sm text-gray-600">
            Powered by Google ADK (`Gemini 3.6 Pro` &amp; `Gemini 3.6 Flash`) • Vertex AI ZDR Active
          </p>
        </div>
      </header>

      <section className="space-y-3">
        {messages.map((msg, idx) => (
          <div key={idx} className="p-3 rounded bg-gray-100">
            {msg}
          </div>
        ))}
        {widgets.map((w, idx) => (
          <WidgetDispatcher key={idx} event={w} />
        ))}
      </section>
    </main>
  );
};

export default App;
