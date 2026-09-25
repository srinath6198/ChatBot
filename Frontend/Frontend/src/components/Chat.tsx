import { useEffect, useRef, useState } from "react";
import type { ChatMessage, ChatSession } from "../api/client";
import {
  createSession,
  getMessages,
  listSessions,
  streamMessage,
} from "../api/client";

export default function Chat() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    initSessions();
  }, []);

  useEffect(() => {
    if (activeSessionId) {
      getMessages(activeSessionId).then(setMessages);
    }
  }, [activeSessionId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  async function initSessions() {
    const existing = await listSessions();
    if (existing.length > 0) {
      setSessions(existing);
      setActiveSessionId(existing[0].id);
    } else {
      const s = await createSession("New Chat");
      setSessions([s]);
      setActiveSessionId(s.id);
    }
  }

  async function handleNewSession() {
    const s = await createSession("New Chat");
    setSessions((prev) => [s, ...prev]);
    setActiveSessionId(s.id);
    setMessages([]);
  }

  async function handleSend() {
    if (!input.trim() || !activeSessionId) return;
    const text = input;
    setInput("");
    setSending(true);

    setMessages((prev) => [
      ...prev,
      { id: `temp-${Date.now()}`, role: "user", content: text, created_at: new Date().toISOString() },
    ]);

    const streamingId = `streaming-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id: streamingId, role: "assistant", content: "", created_at: new Date().toISOString() },
    ]);

    try {
      const sources = await streamMessage(
        activeSessionId,
        text,
        (token) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === streamingId ? { ...m, content: m.content + token } : m
            )
          );
        }
      );
      setMessages((prev) =>
        prev.map((m) => (m.id === streamingId ? { ...m, sources } : m))
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <div style={{ display: "flex", height: "100%", gap: 16 }}>
      <div style={{ width: 200 }}>
        <button onClick={handleNewSession} style={{ width: "100%", marginBottom: 12 }}>
          + New chat
        </button>
        <div className="session-list">
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`session-item ${s.id === activeSessionId ? "active" : ""}`}
              onClick={() => setActiveSessionId(s.id)}
            >
              {s.title}
            </div>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <div className="chat-window" ref={scrollRef}>
          {messages.map((m) => (
            <div key={m.id} className={`msg ${m.role}`}>
              <div>{m.content}</div>
              {m.sources && m.sources.length > 0 && (
                <div className="sources">
                  Sources:{" "}
                  {m.sources
                    .map((s) => `${s.filename} (chunk ${s.chunk_index})`)
                    .join(", ")}
                </div>
              )}
            </div>
          ))}
          {sending && messages[messages.length - 1]?.content === "" && (
            <div className="msg assistant" style={{ color: "#9a9fae" }}>
              Thinking...
            </div>
          )}
        </div>
        <div className="chat-input">
          <input
            value={input}
            placeholder="Ask a question about your documents..."
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            disabled={sending}
          />
          <button onClick={handleSend} disabled={sending || !input.trim()}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}