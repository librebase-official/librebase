"use client";

import { useState } from "react";
import { IconBot, IconSend } from "@/components/studio/icons";

type AgentStep = {
  id: string;
  kind: string;
  status: "ok" | "fail" | "pending" | "skipped";
  message: string;
  detail?: unknown;
};

type ChatMessage = {
  role: "agent" | "user";
  text: string;
  steps?: AgentStep[];
};

const STEP_KIND_LABEL: Record<string, string> = {
  entitlement: "Plan",
  resolve: "Resolve",
  provision: "VM",
  instance: "Instance",
  launch: "Launch",
  probe: "Probe",
  report: "Report",
  decision: "Decision",
};

const STEP_STATUS_DOT: Record<string, string> = {
  ok: "status-dot running",
  fail: "status-dot stopped",
  pending: "status-dot starting",
  skipped: "status-dot",
};

export function AgentChat({
  projectId,
  className,
}: {
  projectId: string;
  className?: string;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "agent",
      text: "I'll run the onboarding chain for this project (entitlements → launch → probe). I only surface business decisions to you.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function send(message: string) {
    if (!message.trim()) return;
    const userMsg: ChatMessage = { role: "user", text: message };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, projectId }),
      });
      const data = (await res.json().catch(() => ({ ok: false }))) as {
        ok?: boolean;
        status?: string;
        summary?: string;
        steps?: AgentStep[];
      };
      const stepMsgs = (data.steps ?? []).map((s) => {
        const label = STEP_KIND_LABEL[s.kind] ?? s.kind;
        const dot = (STEP_STATUS_DOT[s.status] ?? "status-dot");
        return `${label}: ${s.message}`;
      });
      const text = data.ok
        ? `Done (${data.status ?? "ok"}). ${data.summary ?? ""}`
        : `Failed: ${data.summary ?? "see logs"}`;
      setMessages((m) => [
        ...m,
        {
          role: "agent",
          text,
          steps: data.steps ?? [],
        },
      ]);
      void stepMsgs;
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "agent", text: `Error: ${e instanceof Error ? e.message : String(e)}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  const suggested = [
    "Run the onboarding chain",
    "Is everything running?",
    "Show me the connect info",
  ];

  return (
    <div className={`agent-chat ${className ?? ""}`}>
      <div className="agent-chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`agent-msg ${m.role}`}>
            <span className="agent-msg-bubble">
              {m.role === "agent" ? <IconBot className="agent-msg-icon" /> : null}
              <div className="agent-msg-text">
                {m.text}
                {m.steps?.length ? (
                  <ul className="agent-step-list">
                    {m.steps.map((s) => (
                      <li key={s.id} className="agent-step">
                        <span className={STEP_STATUS_DOT[s.status] ?? "status-dot"} />
                        <span className="agent-step-kind">
                          {STEP_KIND_LABEL[s.kind] ?? s.kind}
                        </span>
                        <span className="agent-step-msg">{s.message}</span>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </span>
          </div>
        ))}
      </div>

      <div className="agent-chat-input">
        {messages.length === 1 && (
          <div className="agent-suggested">
            {suggested.map((s) => (
              <button
                key={s}
                type="button"
                className="btn btn-sm btn-ghost"
                onClick={() => send(s)}
                disabled={loading}
              >
                {s}
              </button>
            ))}
          </div>
        )}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="agent-chat-composer"
        >
          <input
            className="input"
            value={input}
            disabled={loading}
            placeholder="Ask the agent…"
            onChange={(e) => setInput(e.target.value)}
          />
          <button
            type="submit"
            className="btn btn-primary btn-icon"
            disabled={loading || !input.trim()}
            aria-label="Send"
            title="Send"
          >
            <IconSend />
          </button>
        </form>
      </div>
    </div>
  );
}
