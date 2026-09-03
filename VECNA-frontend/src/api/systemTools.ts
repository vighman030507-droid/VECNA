import { API_BASE_URL, DEMO_MODE } from "./client";

export type LiveTelemetry = {
  cpu_percent: number;
  ram_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  power_percent: number;
  power_status: string;
  disk_percent: number;
  disk_free_gb: number;
  system_time: string;
  system_date: string;
  uptime: string;
};

export type MemoryItem = {
  id: number;
  text: string;
  created_at: string;
};

export async function fetchLiveTelemetry(): Promise<LiveTelemetry | null> {
  if (DEMO_MODE) {
    return {
      cpu_percent: 18.5,
      ram_percent: 42.1,
      ram_used_gb: 6.7,
      ram_total_gb: 16.0,
      power_percent: 100,
      power_status: "AC Power (100%)",
      disk_percent: 54.0,
      disk_free_gb: 112.5,
      system_time: new Date().toLocaleTimeString(),
      system_date: new Date().toLocaleDateString(),
      uptime: "3h 12m",
    };
  }

  try {
    const res = await fetch(`${API_BASE_URL}/telemetry`);
    if (!res.ok) return null;
    return (await res.json()) as LiveTelemetry;
  } catch {
    return null;
  }
}

export async function analyzeScreen(query: string = "Analyze what is currently on my screen."): Promise<string> {
  if (DEMO_MODE) {
    return "Demo Mode: Screen analysis vision requires live backend with Groq/Gemini key.";
  }

  const res = await fetch(`${API_BASE_URL}/screen/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });

  if (!res.ok) {
    throw new Error("Optical scanner failed to analyze the screen.");
  }
  const body = (await res.json()) as { analysis: string };
  return body.analysis;
}

export async function fetchMemories(): Promise<MemoryItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/memory`);
    if (!res.ok) return [];
    const body = (await res.json()) as { memories: MemoryItem[] };
    return body.memories;
  } catch {
    return [];
  }
}

export async function addMemory(text: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/memory/add`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function executeSystemTool(
  tool: "volume" | "lock_screen" | "media" | "web_search",
  payload: { level?: number; action?: string; query?: string } = {}
): Promise<{ ok: boolean; message: string; data?: any }> {
  const res = await fetch(`${API_BASE_URL}/tools/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool, ...payload }),
  });

  if (!res.ok) {
    throw new Error(`Failed to execute ${tool}`);
  }
  return res.json();
}
