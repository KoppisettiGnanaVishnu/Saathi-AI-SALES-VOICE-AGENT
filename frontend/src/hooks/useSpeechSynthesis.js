import { useCallback, useEffect, useRef, useState } from "react";

export function useSpeechSynthesis() {
  const supported =
    typeof window !== "undefined" && "speechSynthesis" in window;

  const [speaking, setSpeaking] = useState(false);
  const [enabled, setEnabled] = useState(true);
  const voicesRef = useRef([]);

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

  const cancel = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    setSpeaking(false);
  }, [supported]);

  const speak = useCallback(
    (text, lang = "en-IN") => {
      if (!supported || !enabled || !text) return Promise.resolve();

      window.speechSynthesis.cancel();

      return new Promise((resolve) => {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang;
        utterance.rate = 1.02;
        utterance.pitch = 1.0;

        const voices = voicesRef.current.length
          ? voicesRef.current
          : window.speechSynthesis.getVoices();
        const normalized = lang.toLowerCase();
        const languageRoot = normalized.split("-")[0];
        const voice =
          voices.find((item) => item.lang?.toLowerCase() === normalized) ||
          voices.find((item) =>
            item.lang?.toLowerCase().startsWith(languageRoot),
          );

        if (voice) utterance.voice = voice;

        utterance.onstart = () => setSpeaking(true);
        utterance.onend = () => {
          setSpeaking(false);
          resolve();
        };
        utterance.onerror = () => {
          setSpeaking(false);
          resolve();
        };

        window.speechSynthesis.speak(utterance);
      });
    },
    [enabled, supported],
  );

  return { supported, speaking, enabled, setEnabled, speak, cancel };
}
