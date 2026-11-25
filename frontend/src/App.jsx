import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { api } from "./api";
import Composer from "./components/Composer";
import Header from "./components/Header";
import InsightsBar from "./components/InsightsBar";
import LeadPanel from "./components/LeadPanel";
import SummaryPanel from "./components/SummaryPanel";
import Transcript from "./components/Transcript";
import { useSpeechRecognition } from "./hooks/useSpeechRecognition";
import { useSpeechSynthesis } from "./hooks/useSpeechSynthesis";

const STAGE_LABELS = {
  greeting: "Greeting",
  discovery: "Discovery",
  qualification: "Qualification",
  objection_handling: "Objection handling",
  booking: "Booking",
  closing: "Closing",
  closed: "Closed",
};

const uid = () =>
  typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

export default function App() {
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState([]);
  const [lead, setLead] = useState({});
  const [leadScore, setLeadScore] = useState(0);
  const [leadStatus, setLeadStatus] = useState("cold");
  const [sentiment, setSentiment] = useState("neutral");
  const [stage, setStage] = useState("greeting");
  const [booking, setBooking] = useState(null);
  const [slots, setSlots] = useState([]);
  const [knowledgeUsed, setKnowledgeUsed] = useState([]);
  const [crmSyncedAt, setCrmSyncedAt] = useState(null);
  const [language, setLanguage] = useState("en-IN");
  const [busy, setBusy] = useState(false);
  const [starting, setStarting] = useState(true);
  const [callActive, setCallActive] = useState(false);
  const [error, setError] = useState("");
  const [summary, setSummary] = useState(null);
  const [insights, setInsights] = useState(null);
  const [health, setHealth] = useState(null);
  const [text, setText] = useState("");
  const [toast, setToast] = useState("");

  const startedRef = useRef(false);
  const sendRef = useRef(null);

  const {
    speak,
    enqueue: enqueueSpeech,
    cancel: cancelSpeech,
    speaking,
    enabled: voiceEnabled,
    setEnabled: setVoiceEnabled,
    engine: voiceEngine,
    prewarm,
  } = useSpeechSynthesis();

  const {
    supported: sttSupported,
    listening,
    interim,
    error: speechError,
    start: startListening,
    stop: stopListening,
  } = useSpeechRecognition({
    lang: language,
    onFinal: (transcript) => sendRef.current?.(transcript),
  });

  const applyState = useCallback((data) => {
    if (!data) return;
    if (data.lead) setLead(data.lead);
    if (typeof data.lead_score === "number") setLeadScore(data.lead_score);
    if (data.lead_status) setLeadStatus(data.lead_status);
    if (data.sentiment) setSentiment(data.sentiment);
    if (data.stage) setStage(data.stage);
    if (data.booking !== undefined) setBooking(data.booking);
    if (Array.isArray(data.available_slots)) setSlots(data.available_slots);
    if (Array.isArray(data.knowledge_used)) setKnowledgeUsed(data.knowledge_used);
    if (data.crm_synced_at) setCrmSyncedAt(data.crm_synced_at);
  }, []);

  const refreshInsights = useCallback(async () => {
    try {
      setInsights(await api.insights());
    } catch {
      // insights are non-critical
    }
  }, []);

  const refreshHealth = useCallback(async () => {
    try {
      setHealth(await api.health());
    } catch {
      // health is non-critical
    }
  }, []);

  const startSession = useCallback(
    async ({ announce = false } = {}) => {
      setStarting(true);
      setError("");
      setSummary(null);
      setText("");
      setLead({});
      setLeadScore(0);
      setLeadStatus("cold");
      setSentiment("neutral");
      setStage("greeting");
      setBooking(null);
      setSlots([]);
      setKnowledgeUsed([]);
      setCrmSyncedAt(null);
      setMessages([]);

      try {
        const data = await api.createSession();
        setSessionId(data.session_id);
        applyState(data);
        setMessages([
          {
            id: uid(),
            role: "assistant",
            text: data.greeting,
            meta: { stage: "greeting", sentiment: "neutral" },
          },
        ]);
        setCallActive(true);
        if (announce) speak(data.greeting, language);
      } catch (err) {
        setError(
          err.message ||
            "Could not start a call. Make sure the backend is running on port 8000.",
        );
        setCallActive(false);
      } finally {
        setStarting(false);
      }
    },
    [applyState, language, speak],
  );

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    startSession();
    refreshInsights();
    refreshHealth();
  }, [refreshHealth, refreshInsights, startSession]);

  useEffect(() => {
    prewarm(language);
  }, [language, prewarm]);

  useEffect(() => {
    const interval = setInterval(refreshHealth, 30000);
    return () => clearInterval(interval);
  }, [refreshHealth]);

  useEffect(() => {
    if (!toast) return undefined;
    const timeout = setTimeout(() => setToast(""), 3500);
    return () => clearTimeout(timeout);
  }, [toast]);

  const sendMessage = useCallback(
    async (raw) => {
      const message = (raw ?? "").trim();
      if (!message || busy || !sessionId || !callActive) return;

      setError("");
      setBusy(true);
      setText("");
      cancelSpeech();
      stopListening();

      const assistantId = uid();
      setMessages((previous) => [
        ...previous,
        { id: uid(), role: "user", text: message },
        {
          id: assistantId,
          role: "assistant",
          text: "",
          pending: true,
          meta: { stage, sentiment: "neutral", sources: [] },
        },
      ]);

      try {
        let spokenText = "";
        const data = await api.chatStream(
          sessionId,
          message,
          language,
          (event) => {
            if (event.type !== "sentence") return;
            const sentence = String(event.text || "").trim();
            if (!sentence) return;
            spokenText = `${spokenText} ${sentence}`.trim();
            enqueueSpeech(sentence, language);
            setMessages((previous) =>
              previous.map((msg) =>
                msg.id === assistantId
                  ? { ...msg, text: spokenText, pending: false }
                  : msg,
              ),
            );
          },
        );
        applyState(data);
        setMessages((previous) =>
          previous.map((msg) =>
            msg.id === assistantId
              ? {
                  ...msg,
                  text: data.reply,
                  pending: false,
                  meta: {
                    sentiment: data.sentiment,
                    stage: data.stage,
                    sources: data.knowledge_used,
                  },
                }
              : msg,
          ),
        );
        if (data.booking) setToast(`Demo booked · ${data.booking.label}`);
        refreshInsights();
      } catch (err) {
        setMessages((previous) =>
          previous.filter((msg) => !(msg.id === assistantId && !msg.text)),
        );
        setError(err.message || "The agent could not respond. Please try again.");
      } finally {
        setBusy(false);
      }
    },
    [
      applyState,
      busy,
      callActive,
      cancelSpeech,
      enqueueSpeech,
      language,
      refreshInsights,
      sessionId,
      stage,
      stopListening,
    ],
  );

  useEffect(() => {
    sendRef.current = sendMessage;
  }, [sendMessage]);

  const handleBookSlot = useCallback(
    async (slotId) => {
      if (!sessionId || busy || booking) return;
      setBusy(true);
      setError("");
      cancelSpeech();
      stopListening();

      try {
        const data = await api.bookSlot(sessionId, slotId);
        applyState(data);
        setMessages((previous) => [
          ...previous,
          {
            id: uid(),
            role: "assistant",
            text: data.reply,
            meta: { stage: data.stage, sources: [] },
          },
        ]);
        if (data.booking) setToast(`Demo booked · ${data.booking.label}`);
        refreshInsights();
        speak(data.reply, language);
      } catch (err) {
        setError(err.message || "Could not book that slot.");
      } finally {
        setBusy(false);
      }
    },
    [
      applyState,
      booking,
      busy,
      cancelSpeech,
      language,
      refreshInsights,
      sessionId,
      speak,
      stopListening,
    ],
  );

  const handleEndCall = useCallback(async () => {
    if (!sessionId || busy || !callActive) return;
    setBusy(true);
    setError("");
    cancelSpeech();
    stopListening();

    try {
      const data = await api.endCall(sessionId);
      setSummary(data);
      setCallActive(false);
      refreshInsights();
    } catch (err) {
      setError(err.message || "Could not generate the call summary.");
    } finally {
      setBusy(false);
    }
  }, [
    busy,
    callActive,
    cancelSpeech,
    refreshInsights,
    sessionId,
    stopListening,
  ]);

  const handleNewCall = useCallback(() => {
    cancelSpeech();
    stopListening();
    startSession({ announce: true });
    refreshInsights();
  }, [cancelSpeech, refreshInsights, startSession, stopListening]);

  const handleReset = useCallback(async () => {
    if (busy) return;
    if (
      !window.confirm(
        "Clear demo leads, calls and bookings, then start a fresh call?",
      )
    ) {
      return;
    }
    try {
      cancelSpeech();
      stopListening();
      await api.reset();
      await startSession({ announce: true });
      await refreshInsights();
      setToast("Demo data cleared");
    } catch (err) {
      setError(err.message || "Could not reset the demo.");
    }
  }, [
    busy,
    cancelSpeech,
    refreshInsights,
    startSession,
    stopListening,
  ]);

  const handleLanguageChange = useCallback(
    (event) => {
      setLanguage(event.target.value);
      stopListening();
      cancelSpeech();
    },
    [cancelSpeech, stopListening],
  );

  const toggleMic = useCallback(() => {
    if (!callActive || busy || !sttSupported) return;
    if (speaking) cancelSpeech();
    if (listening) stopListening();
    else startListening();
  }, [
    busy,
    callActive,
    cancelSpeech,
    listening,
    speaking,
    startListening,
    sttSupported,
    stopListening,
  ]);

  const quickPrompts = useMemo(
    () =>
      language === "hi-IN"
        ? [
            "मुझे सेल्स कॉल्स के लिए AI एजेंट चाहिए",
            "आपकी कीमत क्या है?",
            "डेटा सुरक्षा कैसे है?",
            "डेमो बुक करें",
          ]
        : [
            "We need an AI agent for inbound sales calls",
            "What does it cost?",
            "How secure is our data?",
            "Book a demo this week",
          ],
    [language],
  );

  return (
    <div className="app">
      <Header
        health={health}
        callActive={callActive}
        busy={busy || starting}
        onEndCall={handleEndCall}
        onNewCall={handleNewCall}
        onReset={handleReset}
        language={language}
        onLanguageChange={handleLanguageChange}
        voiceEnabled={voiceEnabled}
        onToggleVoice={() => setVoiceEnabled((value) => !value)}
        sttSupported={sttSupported}
        voiceEngine={voiceEngine}
        voiceAvailable={health?.voice?.reachable}
      />

      <InsightsBar insights={insights} />

      <main className="workspace">
        <section className="call-card">
          <div className="call-card__top">
            <div className={`live ${callActive ? "live--on" : ""}`}>
              <span className="live__dot" />
              {callActive ? "Live call" : "Call ended"}
            </div>
            <div className="call-card__meta">
              <span className={`pill pill--${leadStatus}`}>{leadStatus}</span>
              <span className="pill pill--stage">
                {STAGE_LABELS[stage] || stage}
              </span>
              <span className={`pill pill--sentiment-${sentiment}`}>
                {sentiment}
              </span>
            </div>
          </div>

          <Transcript
            messages={messages}
            interim={interim}
            busy={busy}
            speaking={speaking}
            starting={starting}
          />

          {error && (
            <div className="error-banner">
              <span>{error}</span>
              <button type="button" onClick={() => setError("")}>
                ✕
              </button>
            </div>
          )}
          {speechError && <div className="hint-banner">{speechError}</div>}

          <Composer
            text={text}
            setText={setText}
            onSend={sendMessage}
            onMic={toggleMic}
            listening={listening}
            interim={interim}
            busy={busy}
            speaking={speaking}
            sttSupported={sttSupported}
            quickPrompts={quickPrompts}
            callActive={callActive}
          />
        </section>

        <LeadPanel
          lead={lead}
          score={leadScore}
          status={leadStatus}
          sentiment={sentiment}
          stage={stage}
          booking={booking}
          slots={slots}
          knowledgeUsed={knowledgeUsed}
          crmSyncedAt={crmSyncedAt}
          busy={busy}
          onBookSlot={handleBookSlot}
        />
      </main>

      <footer className="footer">
        <span>100% open-source MVP · local LLM · browser voice</span>
        <span>Fortivex AI · Round 3 project challenge</span>
      </footer>

      {summary && (
        <SummaryPanel
          data={summary}
          onClose={() => setSummary(null)}
          onNewCall={handleNewCall}
        />
      )}

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
