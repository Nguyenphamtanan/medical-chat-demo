import { useState } from "react";
import axiosClient from "../api/axiosClient";

const RESPONSE_SECTIONS = [
  ["possible_related_systems", "Possible related systems"],
  ["possible_explanations", "Possible explanations"],
  ["red_flags", "Red flags"],
  ["missing_questions", "Missing questions"],
];

const MODEL_STATUS_LABELS = {
  medgemma_real_json: "Phân tích bởi MedGemma",
  medgemma_text_converted_to_json: "Phân tích bởi MedGemma + chuẩn hóa kết quả",
  medgemma_non_json_rule_based_backup: "Kết quả đã được chuẩn hóa",
};

function getModelStatusLabel(status) {
  return MODEL_STATUS_LABELS[status] || null;
}

function ListSection({ title, items }) {
  if (!Array.isArray(items) || items.length === 0) return null;

  return (
    <section className="medical-section">
      <h4>{title}</h4>
      <ul>
        {items.map((item, index) => (
          <li key={`${title}-${index}`}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function MedicalResponse({ data }) {
  if (!data) {
    return <p>No response data returned.</p>;
  }

  const modelStatusLabel = getModelStatusLabel(data.model_status);

  return (
    <article className="medical-response">
      <div className="response-meta">
        <span>Severity: {data.severity || "unknown"}</span>
        {modelStatusLabel && <span>{modelStatusLabel}</span>}
      </div>

      <p className="summary">{data.summary}</p>

      {RESPONSE_SECTIONS.map(([key, title]) => (
        <ListSection key={key} title={title} items={data[key]} />
      ))}

      {data.recommendation && (
        <section className="medical-section">
          <h4>Recommendation</h4>
          <p>{data.recommendation}</p>
        </section>
      )}

      {data.disclaimer && <p className="disclaimer">{data.disclaimer}</p>}
    </article>
  );
}

export default function Chat() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const symptoms = input.trim();
    const userMessage = {
      role: "user",
      content: symptoms,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await axiosClient.post("/chat/ask", {
        symptoms,
      });

      const aiMessage = {
        role: "assistant",
        data: res.data.data?.aiResponse,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          error:
            err.response?.data?.message ||
            "The assistant could not respond. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <main className="chat-container">
      <div className="chat-box">
        {messages.length === 0 && (
          <p className="empty">Enter symptoms to start a medical mini chat.</p>
        )}

        {messages.map((msg, index) => (
          <div key={index} className={`msg ${msg.role}`}>
            {msg.role === "user" ? msg.content : <MedicalResponse data={msg.data} />}
            {msg.error && <p className="error-text">{msg.error}</p>}
          </div>
        ))}

        {loading && <div className="msg assistant">Thinking through the symptoms...</div>}
      </div>

      <div className="chat-input">
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe symptoms, duration, age, severity, and red flags if any..."
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </main>
  );
}
