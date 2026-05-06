import { useEffect, useState } from "react";
import axiosClient from "../api/axiosClient";

export default function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    const fetchHistory = async () => {
      try {
        const res = await axiosClient.get("/chat/history");
        if (isMounted) {
          setHistory(res.data.data);
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
        {history.map((item) => (
          <article className="history-card" key={item._id}>
            <h3>{item.question}</h3>
            <p>
              <strong>Asked:</strong>{" "}
              {new Date(item.createdAt).toLocaleString("en-US")}
            </p>
            <p>
              <strong>Mode:</strong> {item.aiMode || "unknown"} |{" "}
              <strong>Status:</strong> {item.modelStatus || "unknown"}
            </p>

            <details>
              <summary>Input</summary>
              <pre>{JSON.stringify(item.patientInput, null, 2)}</pre>
            </details>

            <details>
              <summary>AI response</summary>
              <pre>{JSON.stringify(item.aiResponse, null, 2)}</pre>
            </details>
          </article>
        ))}
      </div>
    </main>
  );
}
