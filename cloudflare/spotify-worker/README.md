# Spotify Now Playing — Cloudflare Worker

This Worker polls Spotify once per minute and serves the profile card as a dynamic SVG. It replaces GitHub Actions polling after deployment is verified.

## Why Cloudflare

GitHub Actions scheduled workflows have a five-minute minimum. Cloudflare Workers Cron Triggers support `* * * * *` (every minute). Cron execution is UTC and can still be delayed; it is not a real-time guarantee.

## 1. Create a KV namespace

In Cloudflare Dashboard, open **Workers & Pages → KV → Create namespace**. Name it `spotify-state`.

Copy its namespace ID and replace `REPLACE_WITH_CLOUDFLARE_KV_NAMESPACE_ID` in `wrangler.jsonc`.

## 2. Install and authenticate Wrangler

Use Node.js 20.19+ or a currently supported Node.js LTS release:

```bash
npm install
npx wrangler login
```

## 3. Add Spotify secrets

From this directory, set the secrets interactively. Do not commit them or paste them into source files:

```bash
npx wrangler secret put SPOTIFY_CLIENT_ID
npx wrangler secret put SPOTIFY_CLIENT_SECRET
npx wrangler secret put SPOTIFY_REFRESH_TOKEN
```

Use the same Spotify app credentials and refresh token currently stored in GitHub repository secrets. The Worker stores a rotated refresh token in KV if Spotify returns one.

## 4. Deploy

```bash
npx wrangler deploy
```

The deployment output includes a `workers.dev` URL, for example `https://vinayak-spotify-now-playing.<account>.workers.dev`.

## 5. Verify

Open these URLs:

- `https://<worker-url>/health` — should return `{"ok":true,...}`.
- `https://<worker-url>/spotify.svg` — should return the SVG card.

The scheduled trigger runs once per minute. In Cloudflare Dashboard, open the Worker → **Settings → Triggers → Cron Triggers** and verify `* * * * *`. Check **Logs / Events** for scheduled executions.

## 6. Switch the GitHub profile

After the Worker is deployed and `/spotify.svg` returns the expected card, change the Spotify image in the profile README to:

```html
<img src="https://<worker-url>/spotify.svg" width="100%" alt="Spotify currently playing" />
```

GitHub may cache external images, so the profile display can lag behind the Worker even though polling occurs every minute.

## 7. Retire GitHub Actions polling

Only after the README is successfully using the Worker URL, remove the `schedule` block from `.github/workflows/spotify.yml`. Keep `workflow_dispatch` temporarily if you want a manual fallback, or delete the workflow after the Worker has been stable.

## Spotify API considerations

- Polling once per minute is intentionally conservative; Spotify does not provide a playback-change webhook for this use case.
- A Spotify 204 response means there is no active playback and the card changes to the not-playing state.
- A transient Spotify/API error causes the Cron invocation to fail and leaves the last known card intact.
- Never expose Spotify credentials in Git, README files, screenshots, or chat.
