import { useEffect } from "react";

function formatDuration(seconds) {
  const total = Math.max(0, Number(seconds) || 0);
  const minutes = Math.floor(total / 60);
  const remaining = total % 60;
  return minutes ? `${minutes}m ${remaining}s` : `${remaining}s`;
}

function downloadJson(data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `call-summary-${data.session_id || "demo"}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

export default function SummaryPanel({ data, onClose, onNewCall }) {
  const summary = data?.summary || {};
  const points = Array.isArray(summary.key_discussion_points)
    ? summary.key_discussion_points
    : [];
  const objections = Array.isArray(summary.objections)
    ? summary.objections
    : [];

  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="summary-title"
      >
        <div className="modal__head">
          <div>
            <span className="eyebrow">Call complete</span>
            <h2 id="summary-title">Business insights</h2>
            <p className="muted">
              Duration {formatDuration(data?.duration_seconds)} · CRM synced ·
              Summary generated from the live transcript
            </p>
          </div>
          <button
            type="button"
            className="icon-btn"
            onClick={onClose}
            aria-label="Close summary"
          >
            ✕
          </button>
        </div>

        <div className="summary-metrics">
          <div className="summary-metric">
            <span className="summary-metric__label">Lead score</span>
            <strong>{data?.lead_score ?? summary.lead_score ?? 0}</strong>
            <span className={`pill pill--${data?.lead_status || summary.lead_status || "cold"}`}>
              {data?.lead_status || summary.lead_status || "cold"}
            </span>
          </div>
          <div className="summary-metric">
            <span className="summary-metric__label">Sentiment trend</span>
            <strong>{summary.sentiment_trend || "neutral"}</strong>
            <span className="muted">Across the conversation</span>
          </div>
          <div className="summary-metric">
            <span className="summary-metric__label">Meeting</span>
            <strong>{data?.booking ? "Booked" : "Not booked"}</strong>
            <span className="muted">
              {data?.booking ? data.booking.label : "Follow-up required"}
            </span>
          </div>
        </div>

        <section className="summary-block">
          <h3>Executive summary</h3>
          <p>{summary.executive_summary || "No summary available."}</p>
        </section>

        <section className="summary-block">
          <h3>Customer need</h3>
          <p>{summary.customer_need || "Not captured."}</p>
        </section>

        <div className="summary-grid">
          <section className="summary-block">
            <h3>Key discussion points</h3>
            {points.length ? (
              <ul>
                {points.map((point, index) => (
                  <li key={`${point}-${index}`}>{point}</li>
                ))}
              </ul>
            ) : (
              <p className="muted">No points captured.</p>
            )}
          </section>

          <section className="summary-block">
            <h3>Objections</h3>
            {objections.length ? (
              <ul>
                {objections.map((objection, index) => (
                  <li key={`${objection}-${index}`}>{objection}</li>
                ))}
              </ul>
            ) : (
              <p className="muted">None raised.</p>
            )}
          </section>
        </div>

        <section className="summary-block summary-block--next">
          <h3>Next best action</h3>
          <p>{summary.next_action || "Follow up with the lead."}</p>
          <p className="muted">
            {summary.recommended_follow_up || "Send a recap and book a demo."}
          </p>
        </section>

        {data?.booking && (
          <div className="booking-banner">
            📅 Demo booked · {data.booking.label}
          </div>
        )}

        <div className="modal__actions">
          <button
            type="button"
            className="btn btn--ghost"
            onClick={() => downloadJson(data)}
          >
            Download JSON
          </button>
          <button type="button" className="btn btn--primary" onClick={onNewCall}>
            Start new call
          </button>
        </div>
      </div>
    </div>
  );
}
