import { useCallback, useEffect, useRef, useState } from "react";

export type RecorderState = "idle" | "recording" | "processing" | "unsupported" | "error";

const MAX_RECORDING_BYTES = 20 * 1024 * 1024;

export function useRecorder(onRecorded: (blob: Blob) => Promise<void>) {
  const [state, setState] = useState<RecorderState>("idle");
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const bytesRef = useRef(0);
  const exceededLimitRef = useRef(false);

  const stopTracks = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  const start = useCallback(async () => {
    setError(null);
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setState("unsupported");
      setError("Audio recording is not supported in this browser. You can type your order instead.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const preferred = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"].find((type) =>
        MediaRecorder.isTypeSupported(type),
      );
      const recorder = preferred ? new MediaRecorder(stream, { mimeType: preferred }) : new MediaRecorder(stream);
      recorderRef.current = recorder;
      chunksRef.current = [];
      bytesRef.current = 0;
      exceededLimitRef.current = false;
      recorder.ondataavailable = (event) => {
        if (!event.data.size) return;
        if (bytesRef.current + event.data.size > MAX_RECORDING_BYTES) {
          exceededLimitRef.current = true;
          chunksRef.current = [];
          setError("Recording exceeded the local 20 MB safety limit and was discarded. Please type your order instead.");
          setState("error");
          if (recorder.state === "recording") recorder.stop();
          return;
        }
        bytesRef.current += event.data.size;
        chunksRef.current.push(event.data);
      };
      recorder.onerror = () => {
        setState("error");
        setError("Recording stopped unexpectedly. Please type your order or try again.");
        chunksRef.current = [];
        bytesRef.current = 0;
        stopTracks();
      };
      recorder.onstop = () => {
        stopTracks();
        if (exceededLimitRef.current) return;
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "application/octet-stream" });
        chunksRef.current = [];
        bytesRef.current = 0;
        if (blob.size) {
          setState("processing");
          void onRecorded(blob)
            .catch(() => {
              setState("error");
              setError("The recording could not be processed. Please type your order instead.");
            })
            .finally(() => {
              setState((current) => current === "error" ? "error" : "unsupported");
            });
        } else {
          setState("error");
          setError("No audio was captured. Please try again or type your order.");
        }
      };
      recorder.start();
      setState("recording");
    } catch (cause) {
      stopTracks();
      setState("error");
      setError(
        cause instanceof DOMException && cause.name === "NotAllowedError"
          ? "Microphone permission was denied. Allow access in browser settings, or type your order."
          : "Could not access the microphone. You can type your order instead.",
      );
    }
  }, [onRecorded, stopTracks]);

  const stop = useCallback(() => {
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
  }, []);

  useEffect(() => stopTracks, [stopTracks]);

  return { state, error, start, stop };
}
