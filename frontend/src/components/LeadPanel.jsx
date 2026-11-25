const STAGE_ORDER = ["greeting", "discovery", "qualification", "booking", "closing"];

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
  ["call_volume", "Call volume"],
  ["budget", "Budget"],
  ["timeline", "Timeline"],
];

export default function LeadPanel({
  lead,
  score,
  status,
  stage,
  booking,
  slots,
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
  const captured = FIELDS.filter(([key]) => lead?.[key]).length;

  return (
    <aside className="panel" aria-label="Conversation context">
      <section className="panel__section">
        <div className="panel__heading">
          <h2 className="panel__title">Lead</h2>
          <span className={`status-pill status-pill--${status}`}>{status}</span>
        </div>

        <div className="score">
          <div className="score__meta">
            <span className="score__label">Qualification</span>
            <span className="score__value">{clampedScore}<span className="score__max">/100</span></span>
          </div>
          <div className="score__track" role="progressbar" aria-valuenow={clampedScore} aria-valuemin={0} aria-valuemax={100}>
            <div className={`score__bar score__bar--${status}`} style={{ width: `${clampedScore}%` }} />
          </div>
        </div>

        <div className="details">
          {FIELDS.map(([key, label]) => {
            const value = lead?.[key];
            return (
              <div className={`detail ${value ? "detail--filled" : ""}`} key={key}>
                <span className="detail__label">{label}</span>
                <span className="detail__value">{value || "—"}</span>
              </div>
            );
          })}
        </div>
      </section>

      <section className="panel__section">
        <div className="panel__heading">
          <h2 className="panel__title">Stage</h2>
        </div>
        <div className="stages" aria-label="Conversation stage">
          {STAGE_ORDER.map((item, index) => {
            const active = index === stageIndex;
            const done = index < stageIndex;
            return (
              <div className={`stage ${active ? "stage--active" : ""} ${done ? "stage--done" : ""}`} key={item}>
                <span className="stage__dot" aria-hidden="true" />
                <span className="stage__label">{STAGE_LABELS[item]}</span>
              </div>
            );
          })}
        </div>
      </section>

      <section className="panel__section panel__section--booking">
        <div className="panel__heading">
          <h2 className="panel__title">Demo</h2>
          {booking && <span className="status-pill status-pill--booked">Booked</span>}
        </div>

        {booking ? (
          <div className="booking-card">
            <div className="booking-card__label">30-min Fortivex demo</div>
            <div className="booking-card__time">{booking.label}</div>
          </div>
        ) : slots.length > 0 ? (
          <div className="slots">
            {slots.map((slot) => (
              <button type="button" className="slot" key={slot.id} onClick={() => onBookSlot(slot.id)} disabled={busy}>
                <span className="slot__label">{slot.label}</span>
                <span className="slot__action">Book</span>
              </button>
            ))}
          </div>
        ) : (
          <p className="panel__empty">When Saathi offers demo times, clickable slots will appear here and in the chat.</p>
        )}
      </section>

      <div className="panel__footer">
        <span className="panel__footnote">
          {captured.length > 0 ? `${captured.length} detail${captured.length !== 1 ? "s" : ""} captured` : "CRM record updates live"}
          {booking ? " · Demo booked" : ""}
        </span>
      </div>
    </aside>
  );
}
