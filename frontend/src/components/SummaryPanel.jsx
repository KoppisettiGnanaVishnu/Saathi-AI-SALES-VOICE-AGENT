import { useEffect } from "react";

function formatDuration(seconds) {
  const total = Math.max(0, Number(seconds) || 0);
  const minutes = Math.floor(total / 60);
  const remaining = total % 60;
  return minutes ? `${minutes}m ${remaining}s` : `${remaining}s`;
}

function downloadJson(data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `saathi-call-${data.session_id || "summary"}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

export default function SummaryPanel({ data, onClose, onNewCall }) {
  const summary = data?.summary || {};
  const points = Array.isArray(summary.key_discussion_points) ? summary.key_discussion_points : [];
  const objections = Array.isArray(summary.objections) ? summary.objections : [];

  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div
      className="summary-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Call summary"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="summary">
        <div className="summary__header">
          <div>
            <p className="summary__eyebrow">Conversation complete</p>
            <h2>Call summary</h2>
            <p>{formatDuration(data?.duration_seconds)} · {summary.lead_status || "cold"} lead</p>
          </div>
          <button type="button" className="summary__close" onClick={onClose} aria-label="Close summary">×</button>
        </div>

        <div className="summary__grid">
          <div className="summary-stat">
            <span className="summary-stat__label">Lead score</span>
            <span className="summary-stat__value">{data?.lead_score ?? summary.lead_score ?? 0}/100</span>
          </div>
          <div className="summary-stat">
            <span className="summary-stat__label">Sentiment</span>
            <span className="summary-stat__value">{summary.sentiment_trend || data?.sentiment || "neutral"}</span>
          </div>
          <div className="summary-stat">
            <span className="summary-stat__label">Booking</span>
            <span className="summary-stat__value">{data?.booking ? "Booked" : "Not booked"}</span>
          </div>
          <div className="summary-stat">
            <span className="summary-stat__label">CRM</span>
            <span className="summary-stat__value">Synced</span>
          </div>
        </div>

        {(summary.executive_summary || summary.customer_need) && (
          <section className="summary__block">
            <h3>Overview</h3>
            <p className="summary__text">{summary.executive_summary || summary.customer_need}</p>
          </section>
        )}

        <div className="summary__columns">
          <section className="summary__col">
            <h3>Key points</h3>
            {points.length ? (
              <ul className="summary__list">
                {points.map((point, i) => <li key={i}>{point}</li>)}
              </ul>
            ) : <p className="summary__text">No key points captured.</p>}
          </section>
          <section className="summary__col">
            <h3>Objections</h3>
            {objections.length ? (
              <ul className="summary__list summary__list--muted">
                {objections.map((obj, i) => <li key={i}>{obj}</li>)}
              </ul>
            ) : <p className="summary__text">No objections raised.</p>}
          </section>
        </div>

        <section className="summary__block">
          <h3>Next action</h3>
          <p className="summary__text">{summary.next_action || "Follow up with the lead."}</p>
          {summary.recommended_follow_up && <p className="summary__text" style={{ marginTop: 8, color: 'var(--muted)' }}>{summary.recommended_follow_up}</p>}
        </section>

        <div className="summary__actions">
          <button type="button" className="btn btn--ghost" onClick={() => downloadJson(data)}>Download JSON</button>
          <button type="button" className="btn btn--primary" onClick={onNewCall}>New conversation</button>
        </div>
      </div>
    </div>
  );
}
