import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import API from "../services/api";

export default function Chat() {
  const { reportId } = useParams();

  const [sessionId, setSessionId] = useState(null);
  const [messages,  setMessages]  = useState([]);
  const [question,  setQuestion]  = useState("");
  const [loading,   setLoading]   = useState(false);

  const bottomRef  = useRef(null);
  const inputRef   = useRef(null);

  useEffect(() => { createSession(); }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const createSession = async () => {
    try {
      const res = await API.post("/api/sessions", { report_id: reportId });
      setSessionId(res.data.session_id);
      console.log("Session:", res.data.session_id);
    } catch (err) {
      console.error(err);
    }
  };

  const sendMessage = async () => {
    if (!question.trim()) return;
    if (!sessionId) { alert("Session not ready"); return; }

    const userMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    const currentQuestion = question;
    setQuestion("");
    setLoading(true);

    try {
      const res = await API.post("/chat", {
        session_id: sessionId,
        message: currentQuestion,
      });
      setMessages((prev) => [...prev, { role: "assistant", content: res.data.response }]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [...prev, { role: "assistant", content: "Failed to contact chatbot." }]);
    }

    setLoading(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const displayId = reportId ?? "-";

  return (
    <div className="chat-page">

      <div className="chat-header">
        <div>
          <div className="chat-header-title">Report Chat</div>
          <div className="chat-header-sub">
            <span className="chat-report-id">{displayId}</span>
            <span className={`chat-session-dot ${sessionId ? "ready" : "pending"}`} />
            <span className="chat-session-status">
              {sessionId ? "Session active" : "Connecting…"}
            </span>
          </div>
        </div>
      </div>

      <div className="chat-messages">

        {messages.length === 0 && !loading && (
          <div className="chat-empty">
            <div className="chat-empty-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
            </div>
            <p>Ask anything about this report - earnings, risks, metrics, sources.</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`chat-row ${msg.role === "user" ? "chat-row-user" : "chat-row-assistant"}`}
          >
            {msg.role === "assistant" && (
              <div className="chat-avatar chat-avatar-assistant">AI</div>
            )}

            <div className={`chat-bubble ${msg.role === "user" ? "chat-bubble-user" : "chat-bubble-assistant"}`}>
              {msg.content}
            </div>

            {msg.role === "user" && (
              <div className="chat-avatar chat-avatar-user">You</div>
            )}
          </div>
        ))}

        {loading && (
          <div className="chat-row chat-row-assistant">
            <div className="chat-avatar chat-avatar-assistant">AI</div>
            <div className="chat-bubble chat-bubble-assistant chat-bubble-typing">
              <span /><span /><span />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="chat-input-bar">
        <input
          ref={inputRef}
          className="chat-input"
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question…"
          disabled={!sessionId || loading}
        />
        <button
          className="chat-send-btn"
          onClick={sendMessage}
          disabled={!sessionId || loading || !question.trim()}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>

    </div>
  );
}