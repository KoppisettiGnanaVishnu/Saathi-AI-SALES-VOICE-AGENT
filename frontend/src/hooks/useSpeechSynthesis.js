import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Saathi's voice layer.
 *
 * Primary path: the local Kokoro neural voice service through `POST /api/tts`.
 * Replies are split into sentences, the next sentence is synthesised while the
 * current one plays, and clips are cached, so speech starts in well under a
 * second instead of waiting for the whole paragraph.
 *
 * Fallback: the browser's speech synthesiser, with a hand-tuned voice
 * preference list and sentence chunking so it does not sound like a 1990s GPS.
 */

const ACK = {
  en: "Sure.",
  hi: "जी, एक मिनट।",
};

const PREFERRED_VOICES = [
  "Google UK English Female",
  "Google US English",
  "Google हिन्दी",
  "Microsoft Aria Online (Natural)",
  "Microsoft Jenny Online (Natural)",
  "Samantha",
  "Ava",
  "Allison",
  "Serena",
  "Karen",
  "Moira",
  "Tessa",
  "Veena",
  "Rishi",
  "Aman",
  "Tara",
];

const isHindi = (lang) => (lang || "").toLowerCase().startsWith("hi");

function splitSentences(text, maxChars = 190) {
  const cleaned = String(text || "").replace(/\s+/g, " ").trim();
  if (!cleaned) return [];

  const parts = cleaned.match(/[^.!?।]+[.!?।]+|[^.!?।]+$/g) || [cleaned];
  const chunks = [];

  for (const part of parts) {
    let piece = part.trim();
    while (piece.length > maxChars) {
      const comma = piece.lastIndexOf(",", maxChars);
      const space = piece.lastIndexOf(" ", maxChars);
      const cut = Math.max(comma, space);
      const at = cut > 40 ? cut + 1 : maxChars;
      chunks.push(piece.slice(0, at).trim());
      piece = piece.slice(at).trim();
    }
    if (piece) chunks.push(piece);
  }

  // "Sure." on its own sounds clipped; attach very short chunks to the next one.
  const merged = [];
  for (const chunk of chunks) {
    if (merged.length && merged[merged.length - 1].split(" ").length <= 3) {
      merged[merged.length - 1] = `${merged[merged.length - 1]} ${chunk}`.trim();
    } else {
      merged.push(chunk);
    }
  }
  return merged.length ? merged : [cleaned];
}

function pickVoice(voices, lang) {
  const target = (lang || "").toLowerCase();
  const root = target.split("-")[0];
  let best = null;
  let bestScore = -1;

  for (const voice of voices) {
    const voiceLang = (voice.lang || "").toLowerCase();
    let score = 0;
    if (voiceLang === target) score += 6;
    else if (voiceLang.startsWith(root)) score += 3;
    else continue;

    const index = PREFERRED_VOICES.findIndex((name) =>
      (voice.name || "").toLowerCase().includes(name.toLowerCase()),
    );
    if (index >= 0) score += 12 - Math.min(index, 10);
    if (/natural|neural|premium|enhanced/i.test(voice.name || "")) score += 5;
    if (!voice.localService) score += 2;
    if (voice.default) score += 1;

    if (score > bestScore) {
      bestScore = score;
      best = voice;
    }
  }
  return best;
}

export function useSpeechSynthesis() {
  const supported =
    typeof window !== "undefined" && "speechSynthesis" in window;

  const [enabled, setEnabled] = useState(true);
  const [speaking, setSpeaking] = useState(false);
  const [engine, setEngine] = useState("unknown");

  const voicesRef = useRef([]);
  const tokenRef = useRef(0);
  const audioRef = useRef(null);
  const stopRef = useRef(null);
  const cacheRef = useRef(new Map());
  const ackRef = useRef(new Map());
  const neuralRef = useRef(true);
  const speakingRef = useRef(false);
  const queueRef = useRef(Promise.resolve());
  const activeCountRef = useRef(0);

  const beginSpeaking = useCallback(() => {
    activeCountRef.current += 1;
    setSpeaking(true);
  }, []);

  const endSpeaking = useCallback(() => {
    activeCountRef.current = Math.max(0, activeCountRef.current - 1);
    if (activeCountRef.current === 0) setSpeaking(false);
  }, []);

  useEffect(() => {
    speakingRef.current = speaking;
  }, [speaking]);

  useEffect(() => {
    if (!supported) return undefined;

    const loadVoices = () => {
      voicesRef.current = window.speechSynthesis.getVoices();
    };

    loadVoices();
    window.speechSynthesis.addEventListener("voiceschanged", loadVoices);
    return () =>
      window.speechSynthesis.removeEventListener("voiceschanged", loadVoices);
  }, [supported]);

  const stopAudio = useCallback(() => {
    const stop = stopRef.current;
    stopRef.current = null;
    if (stop) stop();

    const audio = audioRef.current;
    audioRef.current = null;
    if (audio) {
      audio.onended = null;
      audio.onerror = null;
      audio.pause();
    }
    if (supported) window.speechSynthesis.cancel();
  }, [supported]);

  const cancel = useCallback(() => {
    tokenRef.current += 1;
    stopAudio();
    queueRef.current = Promise.resolve();
    activeCountRef.current = 0;
    setSpeaking(false);
  }, [stopAudio]);

  const fetchClip = useCallback(async (text, lang) => {
    const key = `${lang}::${text}`;
    const cached = cacheRef.current.get(key);
    if (cached) return cached;

    const response = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, language: lang }),
    });
    if (!response.ok) throw new Error(`tts ${response.status}`);

    const url = URL.createObjectURL(await response.blob());
    cacheRef.current.set(key, url);
    if (cacheRef.current.size > 160) {
      const [oldKey, oldUrl] = cacheRef.current.entries().next().value;
      cacheRef.current.delete(oldKey);
      URL.revokeObjectURL(oldUrl);
    }
    return url;
  }, []);

  const playUrl = useCallback(
    (url) =>
      new Promise((resolve, reject) => {
        const audio = new Audio(url);
        audio.preload = "auto";
        audioRef.current = audio;

        let settled = false;
        const finish = (error) => {
          if (settled) return;
          settled = true;
          if (stopRef.current === finish) stopRef.current = null;
          audio.onended = null;
          audio.onerror = null;
          if (error) reject(error);
          else resolve();
        };

        stopRef.current = finish;
        audio.onended = () => finish();
        audio.onerror = () => finish(new Error("audio playback failed"));
        audio.play().catch((error) => finish(error));
      }),
    [],
  );

  const playNeural = useCallback(
    async (chunks, lang, token) => {
      let pending = fetchClip(chunks[0], lang);
      for (let index = 0; index < chunks.length; index += 1) {
        const url = await pending;
        if (token !== tokenRef.current) return;

        pending =
          index + 1 < chunks.length ? fetchClip(chunks[index + 1], lang) : null;
        if (pending) pending.catch(() => {});

        await playUrl(url);
        if (token !== tokenRef.current) return;
      }
    },
    [fetchClip, playUrl],
  );

  const playBrowser = useCallback(
    async (chunks, lang, token) => {
      const voice = pickVoice(voicesRef.current, lang);
      for (const chunk of chunks) {
        if (token !== tokenRef.current) return;
        await new Promise((resolve) => {
          const utterance = new SpeechSynthesisUtterance(chunk);
          utterance.lang = lang;
          if (voice) utterance.voice = voice;
          utterance.rate = isHindi(lang) ? 0.98 : 1.02;
          utterance.pitch = 1.02;
          utterance.volume = 1;

          let settled = false;
          const done = () => {
            if (settled) return;
            settled = true;
            if (stopRef.current === done) stopRef.current = null;
            resolve();
          };

          utterance.onend = done;
          utterance.onerror = done;
          stopRef.current = done;
          window.speechSynthesis.speak(utterance);
        });
      }
    },
    [],
  );

  const speak = useCallback(
    async (text, lang = "en-IN") => {
      if (!enabled || !text) return;
      const chunks = splitSentences(text);
      if (!chunks.length) return;

      cancel();
      const token = tokenRef.current;
      beginSpeaking();

      try {
        if (neuralRef.current) {
          try {
            await playNeural(chunks, lang, token);
            setEngine("neural");
            return;
          } catch {
            neuralRef.current = false;
            setEngine("browser");
            if (token !== tokenRef.current) return;
          }
        }
        await playBrowser(chunks, lang, token);
      } finally {
        if (token === tokenRef.current) endSpeaking();
      }
    },
    [beginSpeaking, cancel, enabled, endSpeaking, playBrowser, playNeural],
  );

  /** Instant, short acknowledgement so the wait never feels like dead air. */
  const acknowledge = useCallback(
    (lang = "en-IN") => {
      if (!enabled || !neuralRef.current || speakingRef.current) return;
      const token = tokenRef.current;
      beginSpeaking();
      queueRef.current = queueRef.current
        .catch(() => {})
        .then(async () => {
          if (token !== tokenRef.current) return;
          let url = ackRef.current.get(lang);
          if (!url) {
            url = await fetchClip(isHindi(lang) ? ACK.hi : ACK.en, lang);
            ackRef.current.set(lang, url);
          }
          if (token !== tokenRef.current) return;
          await playUrl(url);
        })
        .catch(() => {
          // A missing acknowledgement is harmless.
        })
        .finally(() => {
          if (token === tokenRef.current) endSpeaking();
        });
    },
    [beginSpeaking, enabled, endSpeaking, fetchClip, playUrl],
  );

  /**
   * Enqueue sentences produced by the streaming endpoint. The first sentence
   * starts playing as soon as it is synthesised; later sentences chain on.
   */
  const enqueue = useCallback(
    (text, lang = "en-IN") => {
      if (!enabled || !text) return;
      const chunks = splitSentences(text);
      if (!chunks.length) return;
      const token = tokenRef.current;
      beginSpeaking();

      queueRef.current = queueRef.current
        .catch(() => {})
        .then(async () => {
          if (token !== tokenRef.current) return;
          if (neuralRef.current) {
            try {
              await playNeural(chunks, lang, token);
              if (token === tokenRef.current) setEngine("neural");
              return;
            } catch {
              neuralRef.current = false;
              if (token === tokenRef.current) setEngine("browser");
              if (token !== tokenRef.current) return;
            }
          }
          await playBrowser(chunks, lang, token);
        })
        .finally(() => {
          if (token === tokenRef.current) endSpeaking();
        });
    },
    [beginSpeaking, enabled, endSpeaking, playBrowser, playNeural],
  );

  /** Pre-synthesise the acknowledgement clip so it is instant on the first turn. */
  const prewarm = useCallback(
    (lang = "en-IN") => {
      if (!enabled || !neuralRef.current) return;
      if (ackRef.current.has(lang)) return;
      fetchClip(isHindi(lang) ? ACK.hi : ACK.en, lang)
        .then((url) => ackRef.current.set(lang, url))
        .catch(() => {});
    },
    [enabled, fetchClip],
  );

  useEffect(() => {
    const cache = cacheRef.current;
    return () => {
      tokenRef.current += 1;
      stopAudio();
      for (const url of cache.values()) URL.revokeObjectURL(url);
      cache.clear();
    };
  }, [stopAudio]);

  return {
    supported,
    speaking,
    enabled,
    setEnabled,
    engine,
    speak,
    enqueue,
    cancel,
    acknowledge,
    prewarm,
  };
}
