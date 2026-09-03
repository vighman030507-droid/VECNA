export type Voice = { id: string; label: string };
import { API_BASE_URL, DEMO_MODE } from "./client";

export async function fetchVoices(): Promise<Voice[]> {
  if (DEMO_MODE) {
    return [
      { id: "demo-guy", label: "Guy — Demo Voice" },
      { id: "demo-jenny", label: "Jenny — Demo Voice" },
    ];
  }
  const response = await fetch(`${API_BASE_URL}/voices`);
  if (!response.ok) throw new Error("Voice options are unavailable.");
  const body = await response.json() as { voices: Voice[] };
  return body.voices;
}

export async function requestSpeech(
  text: string,
  voiceId: string,
  language: "en" | "hi" = "en",
  angerLevel: number = 0,
): Promise<Blob> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voiceId, language, angerLevel }),
    });
  } catch {
    throw new Error("Speech service is unavailable.");
  }
  if (!response.ok) throw new Error("Speech generation is unavailable. The text reply is still available.");
  return response.blob();
}

export async function transcribeRecording(audio: Blob, language: "en" | "hi" = "en"): Promise<string> {
  const form = new FormData();

  // Derive a clean filename extension from the actual blob MIME type
  // so the backend can reliably detect the audio container format.
  const mime = audio.type.split(";")[0].trim(); // strip codec params
  const extMap: Record<string, string> = {
    "audio/webm": "webm",
    "audio/mp4": "mp4",
    "audio/ogg": "ogg",
    "audio/wav": "wav",
    "audio/wave": "wav",
    "audio/x-wav": "wav",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
  };
  const ext = extMap[mime] ?? "webm";
  form.append("audio", audio, `recording.${ext}`);
  form.append("language", language);  // Whisper acoustic model hint

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/transcribe`, { method: "POST", body: form });
  } catch {
    throw new Error("Speech transcription service is unavailable.");
  }
  if (!response.ok) {
    const body: { detail?: string } = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? "Vecna could not transcribe that recording.");
  }
  return (await response.json() as { transcript: string }).transcript;
}
