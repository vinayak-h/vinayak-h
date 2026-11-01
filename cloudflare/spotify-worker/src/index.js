const TOKEN_URL = "https://accounts.spotify.com/api/token";
const PLAYBACK_URL = "https://api.spotify.com/v1/me/player/currently-playing";
const STATE_KEY = "spotify:now-playing";

function xml(value = "") {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;"
  })[char]);
}

function renderCard(state) {
  const playing = Boolean(state?.is_playing && state?.track);
  const title = playing ? state.track : "Not listening to Spotify right now";
  const subtitle = playing
    ? [state.artist, state.album].filter(Boolean).join(" · ")
    : "When playback starts, the current track will appear here.";
  const note = playing
    ? "NOW PLAYING · " + new Date(state.updated_at).toISOString().slice(11, 16) + " UTC"
    : "NOT PLAYING";
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="112" viewBox="0 0 1000 112">
<rect width="100%" height="100%" rx="12" fill="#0B0B0C" stroke="#303036"/>
<circle cx="52" cy="56" r="20" fill="#202124"/>
<path d="M42 49c12-4 23-1 29 4M44 56c9-3 18-1 24 3M46 63c7-2 13-1 19 2" fill="none" stroke="#A1A1AA" stroke-width="2" stroke-linecap="round"/>
<text x="88" y="48" fill="#F4F4F5" font-size="17" font-weight="600" font-family="Inter,Segoe UI,Arial">${xml(title)}</text>
<text x="88" y="73" fill="#A1A1AA" font-size="13" font-family="Inter,Segoe UI,Arial">${xml(subtitle)}</text>
<text x="972" y="95" text-anchor="end" fill="#71717A" font-size="10" font-family="Inter,Segoe UI,Arial">${xml(note)}</text>
</svg>`;
}

async function getRefreshToken(env) {
  return await env.SPOTIFY_STATE.get("refresh_token") || env.SPOTIFY_REFRESH_TOKEN;
}

async function refreshAccessToken(env) {
  const refreshToken = await getRefreshToken(env);
  if (!env.SPOTIFY_CLIENT_ID || !env.SPOTIFY_CLIENT_SECRET || !refreshToken) {
    throw new Error("Missing Spotify Worker secrets.");
  }
  const credentials = btoa(`${env.SPOTIFY_CLIENT_ID}:${env.SPOTIFY_CLIENT_SECRET}`);
  const response = await fetch(TOKEN_URL, {
    method: "POST",
    headers: {
      Authorization: `Basic ${credentials}`,
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: refreshToken
    })
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Spotify token refresh failed (HTTP ${response.status}): ${detail.slice(0, 300)}`);
  }
  const payload = await response.json();
  if (payload.refresh_token && payload.refresh_token !== refreshToken) {
    await env.SPOTIFY_STATE.put("refresh_token", payload.refresh_token);
  }
  return payload.access_token;
}

async function updatePlayback(env) {
  const accessToken = await refreshAccessToken(env);
  const response = await fetch(PLAYBACK_URL, {
    headers: { Authorization: `Bearer ${accessToken}` }
  });

  if (response.status === 204 || response.status === 404) {
    await env.SPOTIFY_STATE.put(STATE_KEY, JSON.stringify({
      is_playing: false,
      updated_at: new Date().toISOString()
    }));
    return;
  }
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Spotify playback request failed (HTTP ${response.status}): ${detail.slice(0, 300)}`);
  }

  const payload = await response.json();
  const item = payload?.item;
  if (!payload?.is_playing || !item) {
    await env.SPOTIFY_STATE.put(STATE_KEY, JSON.stringify({
      is_playing: false,
      updated_at: new Date().toISOString()
    }));
    return;
  }

  await env.SPOTIFY_STATE.put(STATE_KEY, JSON.stringify({
    is_playing: true,
    track: item.name || "Unknown track",
    artist: (item.artists || []).map((artist) => artist.name).filter(Boolean).join(", "),
    album: item.album?.name || "",
    updated_at: new Date().toISOString()
  }));
}

export default {
  async scheduled(controller, env) {
    await updatePlayback(env);
    console.log("Spotify playback refreshed", new Date(controller.scheduledTime).toISOString());
  },

  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") {
      return Response.json({ ok: true, service: "spotify-now-playing-worker" }, {
        headers: { "Cache-Control": "no-store" }
      });
    }
    if (url.pathname !== "/" && url.pathname !== "/spotify.svg") {
      return new Response("Not found", { status: 404 });
    }

    const raw = await env.SPOTIFY_STATE.get(STATE_KEY);
    const state = raw ? JSON.parse(raw) : null;
    return new Response(renderCard(state), {
      headers: {
        "Content-Type": "image/svg+xml; charset=utf-8",
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "CDN-Cache-Control": "no-store",
        "Access-Control-Allow-Origin": "*"
      }
    });
  }
};
