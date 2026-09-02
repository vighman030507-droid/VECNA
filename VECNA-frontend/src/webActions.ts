import { API_BASE_URL } from "./api/client";

export type WebAction = {
  kind:
    | "open_website"
    | "web_search"
    | "youtube_search"
    | "spotify_search"
    | "hotstar_search"
    | "prime_video_search"
    | "netflix_search"
    | "jiocinema_search"
    | "github_search"
    | "reddit_search"
    | "twitch_search"
    | string;
  label: string;
  url: string;
};

const knownWebsitesPattern =
  /\b(youtube|spotify|google|reddit|twitter|x\.com|github|wikipedia|netflix|amazon|prime\s*video|hotstar|jiohotstar|jiocinema|twitch|instagram|facebook|linkedin|discord|gmail)\b/i;
const domainPattern =
  /(?:https?:\/\/|www\.)?[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:com|org|net|io|edu|gov|dev|app|co|ai|in)(?:\/[^\s]*)?/i;
const explicitUrlPattern = /https?:\/\/[^\s]+/i;
const searchOnPlatformPattern =
  /\b(on|in|using|via)\s+(google|youtube|spotify|hotstar|jiohotstar|jiocinema|netflix|prime\s*video|amazon|github|reddit|twitch|the web|the internet)\b/i;
const searchPrefixPattern =
  /^(?:please\s+)?(?:can you\s+)?(?:search|find|lookup|look up|google|play|watch|stream)\s+/i;
const openWebsitePrefixPattern =
  /^(?:please\s+)?(?:can you\s+)?(?:open|launch|start|go to|visit|browse to|navigate to)\s+/i;

export function isCapabilityQuery(text: string): boolean {
  const normalized = text.trim().toLowerCase();
  return (
    /\b(what|which|list|tell me|show me|how many)\b.*\b(apps?|applications?|desktop|web apps?|websites?|capabilities|features?|actions?|do|open|launch)\b/i.test(
      normalized,
    ) ||
    /^(what|which)\s+(can|do)\s+you\s+(open|launch|do)/i.test(normalized) ||
    /\bwhat\s+can\s+you\s+(open|do|launch)\b/i.test(normalized)
  );
}

export function isWebActionRequest(text: string): boolean {
  const trimmed = text.trim();
  if (!trimmed || isCapabilityQuery(trimmed)) return false;

  // Explicit URL provided
  if (explicitUrlPattern.test(trimmed) || domainPattern.test(trimmed)) {
    return true;
  }

  // Explicit search targeting a platform or web
  if (searchOnPlatformPattern.test(trimmed)) {
    return true;
  }

  // Any command referencing a known platform with action keyword
  if (
    knownWebsitesPattern.test(trimmed) &&
    /\b(open|launch|start|play|watch|stream|search|find|listen|go to|visit|browse)\b/i.test(trimmed)
  ) {
    return true;
  }

  // "Search / Google / Play / Watch / Stream / Find" command
  if (searchPrefixPattern.test(trimmed)) {
    return true;
  }

  // "Open / Go to / Visit <website>"
  if (
    openWebsitePrefixPattern.test(trimmed) &&
    (knownWebsitesPattern.test(trimmed) || /\b(website|url|webpage|page|site)\b/i.test(trimmed))
  ) {
    return true;
  }

  return false;
}

export async function planWebAction(text: string): Promise<WebAction> {
  const response = await fetch(`${API_BASE_URL}/web-actions/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) throw new Error("VECNA could not prepare that web action.");
  return response.json() as Promise<WebAction>;
}
