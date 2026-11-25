export default function InsightsBar({ insights }) {
  const items = [
    { label: "Total leads", value: insights?.total_leads },
    { label: "Hot leads", value: insights?.hot_leads, tone: "tone--hot" },
    {
      label: "Meetings booked",
      value: insights?.meetings_booked,
      tone: "tone--ok",
    },
    { label: "Avg lead score", value: insights?.avg_score },
    {
      label: "Positive sentiment",
      value:
        insights && typeof insights.positive_sentiment_pct === "number"
          ? `${insights.positive_sentiment_pct}%`
          : null,
      tone: "tone--ok",
    },
  ];

  return (
    <section className="insights" aria-label="Live pipeline insights">
      <div className="insights__title">
        <span className="pulse" />
        Live pipeline
      </div>
      <div className="insights__grid">
        {items.map((item) => (
          <div className="stat" key={item.label}>
            <span className="stat__label">{item.label}</span>
            <span className={`stat__value ${item.tone || ""}`}>
              {item.value ?? "—"}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
