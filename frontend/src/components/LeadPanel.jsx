const STAGE_ORDER = [
  "greeting",
  "discovery",
  "qualification",
  "booking",
  "closing",
];

const STAGE_LABELS = {
  greeting: "Greeting",
  discovery: "Discovery",
  qualification: "Qualification",
  booking: "Booking",
  closing: "Closing",
};

const FIELDS = [
  ["name", "Name"],
  ["company", "Company"],
  ["need", "Need"],
  ["budget", "Budget"],
  ["timeline", "Timeline"],
  ["decision_role", "Decision role"],
  ["email", "Email"],
  ["phone", "Phone"],
];

function timeAgo(iso) {
  if (!iso) return null;
  const timestamp = new Date(iso).getTime();
  if (Number.isNaN(timestamp)) return null;
  const seconds = Math.max(0, Math.floor((Date.now() - timestamp) / 1000));
  if (seconds < 10) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

export default function LeadPanel({
  lead,
  score,
  status,
  sentiment,
  stage,
  booking,
  slots,
  knowledgeUsed,
  crmSyncedAt,
  busy,
  onBookSlot,
}) {
  const clampedScore = Math.max(0, Math.min(100, Number(score) || 0));
  const stageIndex =
    stage === "closed"
      ? STAGE_ORDER.length
      : stage === "objection_handling"
        ? 2
        : Math.max(0, STAGE_ORDER.indexOf(stage));
  const filled = FIELDS.filter(([key]) => lead?.[key]).length;
  const sources = [...new Set(knowledgeUsed || [])].slice(0, 4);

  return (
    <aside className="lead-panel">
      <div className="lead-panel__head">
        <div>
          <span className="eyebrow">CRM record</span>
          <h2>Lead profile</h2>
        </div>
        <span className={`pill pill--${status}`}>{status}</span>
      </div>

      <div className="score-row">
        <div className="score-ring" style={{ "--score": clampedScore }}>
          <div className="score-ring__inner">
            <span>{clampedScore}</span>
            <small>/100</small>
          </div>
        </div>
        <div className="score-copy">
          <strong>Lead score</strong>
          <p>
            Deterministic score from need, budget, timeline, authority, company
            and sentiment.
          </p>
        </div>
      </div>

      <div className="stage-block">
        <div className="stage-block__head">
          <span>Conversation stage</span>
          <span className={`sentiment sentiment--${sentiment}`}>
            {sentiment}
          </span>
        </div>
        <div className="stage-track">
          {STAGE_ORDER.map((item, index) => (
            <div
              className={`stage-step ${
                index <= stageIndex ? "stage-step--done" : ""
              } ${index === stageIndex ? "stage-step--active" : ""}`}
              key={item}
            >
              <span className="stage-step__dot" />
              <span className="stage-step__label">{STAGE_LABELS[item]}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="crm-row">
        <span className={`crm-dot ${crmSyncedAt ? "crm-dot--on" : ""}`} />
        <span>
          {crmSyncedAt
            ? `CRM synced ${timeAgo(crmSyncedAt)}`
            : "CRM awaiting first update"}
        </span>
      </div>

      {booking && (
        <div className="booking-card">
          <span className="booking-card__icon">📅</span>
          <div>
            <strong>Demo booked</strong>
            <span>{booking.label}</span>
          </div>
        </div>
      )}

      <div className="panel-section">
        <div className="panel-section__head">
          <h3>Captured details</h3>
          <span>{filled}/8</span>
        </div>
        <div className="fields">
          {FIELDS.map(([key, label]) => (
            <div
              className={`field ${key === "need" ? "field--wide" : ""}`}
              key={key}
            >
              <span className="field__label">{label}</span>
              <span
                className={`field__value ${lead?.[key] ? "" : "field__value--empty"}`}
                title={lead?.[key] || ""}
              >
                {lead?.[key] || "—"}
              </span>
            </div>
          ))}
        </div>
      </div>

      {!booking && slots.length > 0 && (
        <div className="panel-section">
          <div className="panel-section__head">
            <h3>Available demo slots</h3>
            <span>{slots.length}</span>
          </div>
          <div className="slot-list">
            {slots.slice(0, 4).map((slot) => (
              <div className="slot" key={slot.id}>
                <span>{slot.label}</span>
                <button
                  type="button"
                  className="slot__btn"
                  onClick={() => onBookSlot(slot.id)}
                  disabled={busy}
                >
                  Book
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {sources.length > 0 && (
        <div className="panel-section">
          <div className="panel-section__head">
            <h3>Grounded on</h3>
          </div>
          <div className="chips">
            {sources.map((source) => (
              <span className="source-chip" key={source}>
                📄 {source}
              </span>
            ))}
          </div>
        </div>
      )}

      <p className="panel-note">
        Updates sync to the CRM after every turn. In production this adapter
        writes to HubSpot or Salesforce.
      </p>
    </aside>
  );
}
