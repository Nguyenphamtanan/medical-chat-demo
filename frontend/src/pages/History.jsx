import { useEffect, useState } from "react";
import axiosClient from "../api/axiosClient";

const EMPTY_TEXT = "Không có nội dung";

function formatDate(value) {
  if (!value) return EMPTY_TEXT;
  return new Date(value).toLocaleString("en-US");
}

function getMessages(conversation, role) {
  return Array.isArray(conversation.messages)
    ? conversation.messages.filter((message) => message.role === role)
    : [];
}

function getLatestAssistant(conversation) {
  const assistantMessages = getMessages(conversation, "assistant");
  return assistantMessages[assistantMessages.length - 1] || null;
}

function renderMessageContent(messages) {
  if (!messages.length) return EMPTY_TEXT;
  return messages.map((message) => message.content || EMPTY_TEXT).join("\n\n");
}

function LegacyHistoryCard({ item }) {
  return (
    <article className="history-card">
      <h3>{item.question || "Legacy chat"}</h3>
      <p>
        <strong>Asked:</strong> {formatDate(item.createdAt)}
      </p>
      <p>
        <strong>Mode:</strong> {item.aiMode || "unknown"} |{" "}
        <strong>Status:</strong> {item.modelStatus || "unknown"}
      </p>
      <details>
        <summary>Input</summary>
        <pre>{JSON.stringify(item.patientInput || EMPTY_TEXT, null, 2)}</pre>
      </details>
      <details>
        <summary>AI response</summary>
        <pre>{JSON.stringify(item.aiResponse || EMPTY_TEXT, null, 2)}</pre>
      </details>
    </article>
  );
}

function ConversationHistoryCard({ conversation }) {
  const userMessages = getMessages(conversation, "user");
  const assistantMessages = getMessages(conversation, "assistant");
  const latestAssistant = getLatestAssistant(conversation);
  const metadata = latestAssistant?.metadata || {};

  return (
    <article className="history-card">
      <h3>{conversation.title || EMPTY_TEXT}</h3>
      <p>
        <strong>Updated:</strong>{" "}
        {formatDate(conversation.updatedAt || conversation.createdAt)}
      </p>
      <p>
        <strong>Mode:</strong> {metadata.mode || EMPTY_TEXT} |{" "}
        <strong>Status:</strong> {metadata.modelStatus || EMPTY_TEXT}
      </p>

      <details>
        <summary>Input</summary>
        <pre>{renderMessageContent(userMessages)}</pre>
      </details>

      <details>
        <summary>AI response</summary>
        <pre>{renderMessageContent(assistantMessages)}</pre>
      </details>
    </article>
  );
}

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchHistory = async () => {
      try {
        const res = await axiosClient.get("/chat/history");
        if (isMounted) {
          setHistory(res.data.data || []);
        }
      } catch (error) {
        console.error("Error loading history:", error);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchHistory();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <main className="history-page">
      <h1>Chat History</h1>

      {loading && <p>Loading...</p>}

      {!loading && history.length === 0 && (
        <p className="muted">No medical chat history yet.</p>
      )}

      <div className="history-list">
        {history.map((item) =>
          Array.isArray(item.messages) ? (
            <ConversationHistoryCard conversation={item} key={item._id} />
          ) : (
            <LegacyHistoryCard item={item} key={item._id} />
          )
        )}
      </div>
    </main>
  );
}
