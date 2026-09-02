export type ChatResponse = {
  sessionId: string;
  reply: string;
  corruptedReply: string;
  fearLevel: 1 | 2 | 3;
  curseActive: boolean;
  turnsRetained: number;
  angerLevel: number;
};

import { API_BASE_URL, DEMO_MODE } from "./client";

function getDemoReply(text: string): { reply: string; corruptedReply: string } {
  const lower = text.toLowerCase();

  if (lower.includes("hello") || lower.includes("hi")) {
    return {
      reply: "Your time is running short. Do not test my patience, mortal.",
      corruptedReply: "Y̷o̷u̷r̷ time is running short. Do not test my patience, mortal.",
    };
  }

  if (lower.includes("what can you do")) {
    return {
      reply: "I control the gateway to the Upside Down. I can open your applications, scour the web, and seal your fate.",
      corruptedReply: "I control the g̷a̷t̷e̷w̷a̷y̷ to the Upside Down. I can open your applications, scour the web, and seal your f̷a̷t̷e̷.",
    };
  }

  return {
    reply: `You dare summon me with "${text}"? The clock is already ticking.`,
    corruptedReply: `You dare summon me with "${text}"? The c̷l̷o̷c̷k̷ is already ticking.`,
  };
}

export async function sendChatMessage(
  sessionId: string,
  text: string,
  language: "en" | "hi" = "en",
): Promise<ChatResponse> {
  if (DEMO_MODE) {
    await new Promise((resolve) => setTimeout(resolve, 700));
    const demo = getDemoReply(text);
    return {
      sessionId,
      reply: demo.reply,
      corruptedReply: demo.corruptedReply,
      fearLevel: 1,
      curseActive: false,
      turnsRetained: 0,
      angerLevel: 0,
    };
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId, text, language }),
    });
  } catch {
    throw new Error("VECNA backend service is unavailable. Please check your server.");
  }

  if (!response.ok) {
    const body: { detail?: string } = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? "VECNA could not process that message.");
  }

  return response.json() as Promise<ChatResponse>;
}
