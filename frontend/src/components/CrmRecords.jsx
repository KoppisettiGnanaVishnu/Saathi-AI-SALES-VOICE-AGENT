import { useCallback, useEffect, useState } from "react";
import { api } from "../api";

export default function CrmRecords({ refreshKey }) {
  const [open, setOpen] = useState(true);
  const [leads, setLeads] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [l, a, c] = await Promise.all([
        api.leads(),
        api.appointments(),
        api.calls(),
      ]);
      setLeads(l.leads || []);
      setAppointments(a.appointments || []);
      setCalls(c.calls || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  return (
    <section className="crm-records">
      <button type="button" className="crm-records__toggle" onClick={() => setOpen((v) => !v)}>
        <span>CRM Records</span>
        <span className="crm-records__chevron">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div className="crm-records__body">
          {loading && <p className="crm-records__loading">Loading…</p>}
          <div className="crm-records__grid">
            <div className="crm-records__card">
              <h3>Leads ({leads.length})</h3>
              {leads.length === 0 ? <p className="crm-records__empty">No leads yet.</p> : (
                <ul className="crm-records__list">
                  {leads.map((l) => (
                    <li key={l.session_id} className="crm-records__item">
                      <strong>{l.name || "Unknown"}</strong>
                      {l.company ? ` · ${l.company}` : ""}
                      <div className="crm-records__meta">
                        Score {l.score} · {l.status} · {l.stage}
                        {l.call_volume ? ` · ${l.call_volume} calls` : ""}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="crm-records__card">
              <h3>Demo Bookings ({appointments.length})</h3>
              {appointments.length === 0 ? <p className="crm-records__empty">No bookings yet.</p> : (
                <ul className="crm-records__list">
                  {appointments.map((a) => (
                    <li key={a.id || a.slot_id} className="crm-records__item">
                      <strong>{a.slot_iso ? new Date(a.slot_iso).toLocaleString() : a.slot_id}</strong>
                      <div className="crm-records__meta">
                        {a.session_id} · {a.status || "booked"}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="crm-records__card crm-records__card--wide">
              <h3>Call Summaries ({calls.length})</h3>
              {calls.length === 0 ? <p className="crm-records__empty">No completed calls yet. End a call to generate a summary.</p> : (
                <ul className="crm-records__list">
                  {calls.map((c) => (
                    <li key={c.session_id} className="crm-records__item">
                      <strong>{c.session_id}</strong>
                      <div className="crm-records__meta">
                        {c.duration_seconds}s · {c.created_at}
                      </div>
                      <p className="crm-records__summary">
                        {c.summary?.executive_summary || c.summary?.summary || "Summary available"}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}