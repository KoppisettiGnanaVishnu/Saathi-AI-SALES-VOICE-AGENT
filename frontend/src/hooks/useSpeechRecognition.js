import { useCallback, useEffect, useRef, useState } from "react";

export function useSpeechRecognition({ lang = "en-IN", onFinal }) {
  const Recognition =
    typeof window !== "undefined"
      ? window.SpeechRecognition || window.webkitSpeechRecognition
      : null;
  const supported = Boolean(Recognition);

  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const [error, setError] = useState("");

  const recognitionRef = useRef(null);
  const onFinalRef = useRef(onFinal);

  useEffect(() => {
    onFinalRef.current = onFinal;
  }, [onFinal]);

  useEffect(() => {
    if (!supported) return undefined;

    const recognition = new Recognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.lang = lang;

    recognition.onstart = () => {
      setListening(true);
      setError("");
    };

    recognition.onresult = (event) => {
      let finalText = "";
      let interimText = "";
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const transcript = event.results[index][0].transcript;
        if (event.results[index].isFinal) finalText += transcript;
        else interimText += transcript;
      }
      if (interimText) setInterim(interimText.trim());
      if (finalText.trim()) {
        setInterim("");
        onFinalRef.current?.(finalText.trim());
      }
    };

    recognition.onerror = (event) => {
      if (event.error === "no-speech") {
        setError("No speech detected. Try again.");
      } else if (
        event.error === "not-allowed" ||
        event.error === "service-not-allowed"
      ) {
        setError("Microphone permission denied. Allow mic access and retry.");
      } else if (event.error === "audio-capture") {
        setError("No microphone found. Check your input device.");
      } else if (event.error !== "aborted") {
        setError(`Voice input error: ${event.error}`);
      }
      setListening(false);
      setInterim("");
    };

    recognition.onend = () => {
      setListening(false);
      setInterim("");
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.abort();
      } catch {
        // ignore cleanup errors
      }
      recognitionRef.current = null;
    };
  }, [Recognition, lang, supported]);

  const start = useCallback(() => {
    if (!recognitionRef.current) return;
    setError("");
    try {
      recognitionRef.current.start();
    } catch {
      // recognition may already be running
    }
  }, []);

  const stop = useCallback(() => {
    try {
      recognitionRef.current?.stop();
    } catch {
      // ignore
    }
  }, []);

  return { supported, listening, interim, error, start, stop };
}
