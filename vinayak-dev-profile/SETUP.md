# Vinayak.dev — GitHub profile README package

This package is a GitHub Profile README for `vinayak-h/vinayak-h`, with supporting GitHub Actions workflows. It is not a standalone website: GitHub README pages render Markdown, images, links and supported HTML such as `<details>`, but do not execute arbitrary JavaScript or React.

## Included

- `README.md` — minimal monochrome profile with subtle neutral accents.
- `.github/workflows/snake.yml` — generates contribution snake SVGs on the `output` branch.
- `.github/workflows/profile-metrics.yml` — refreshes public account/repository metrics daily.
- `.github/workflows/spotify.yml` — optional Spotify now-playing panel refresh every five minutes.
- `scripts/generate_metrics.py` — fetches public GitHub REST API data and generates `assets/github-metrics.svg`.
- `scripts/update_spotify.py` — fetches Spotify playback and generates `assets/spotify.svg`.
- `scripts/spotify_auth.py` — one-time local helper to obtain a Spotify refresh token.
- `assets/*.svg` — honest first-run placeholders; no invented metrics or track information.

## 1. Copy into your profile repository

Clone the repository and copy the **contents** of this ZIP into its root. Include hidden folders such as `.github`.

```bash
git clone https://github.com/vinayak-h/vinayak-h.git
cd vinayak-h
# Copy extracted package contents into this directory.
git add README.md .github scripts assets SETUP.md
git commit -m "feat: build minimal developer profile with live integrations"
git push origin main
```

## 2. Enable GitHub Actions write permissions

In the repository, open **Settings → Actions → General → Workflow permissions**. Select **Read and write permissions** and save. Then open **Actions** and manually run:

1. `Generate contribution snake`
2. `Update profile metrics`

The snake workflow publishes SVGs to a separate `output` branch. The README references:
`https://raw.githubusercontent.com/vinayak-h/vinayak-h/output/github-contribution-grid-snake.svg`

The metrics workflow fetches public account/repository data from `api.github.com` and commits the generated SVG to `main`. Its language summary counts repository language metadata, not source-code lines or time spent coding.

## 3. Optional Spotify integration

The README works without Spotify. To activate it:

1. Create an app at https://developer.spotify.com/dashboard.
2. Add this exact Redirect URI: `http://127.0.0.1:8888/callback`.
3. Use scopes `user-read-currently-playing` and `user-read-playback-state`.
4. On your own computer, set the Spotify client ID and secret as environment variables, then run `python scripts/spotify_auth.py` (or `python3` on macOS/Linux).
5. Authorize in the browser. The script prints a refresh token.
6. In **Repository → Settings → Secrets and variables → Actions**, add:
   - `SPOTIFY_CLIENT_ID`
   - `SPOTIFY_CLIENT_SECRET`
   - `SPOTIFY_REFRESH_TOKEN`
7. Run the `Update Spotify now playing` workflow manually.

Windows PowerShell:

```powershell
$env:SPOTIFY_CLIENT_ID="your-client-id"
$env:SPOTIFY_CLIENT_SECRET="your-client-secret"
python scripts/spotify_auth.py
```

macOS/Linux:

```bash
export SPOTIFY_CLIENT_ID="your-client-id"
export SPOTIFY_CLIENT_SECRET="your-client-secret"
python3 scripts/spotify_auth.py
```

The workflow updates every five minutes. If no playback is active, the card explicitly reports that. Spotify API access and developer-app eligibility are subject to Spotify's current policies. This integration displays playback only; it does not control Spotify.

## Data integrity

- GitHub metrics come from GitHub's public REST API.
- Language counts represent repository metadata, not code-volume percentages.
- Third-party GitHub stats/streak cards can be rate-limited or unavailable.
- Spotify is optional and remains a clear setup placeholder until valid secrets are configured.
- Contribution snake is generated from GitHub contribution data by the `Platane/snk` action.
- Project descriptions are intentionally conservative. Verify KnowledgeBridge's current stack and description before publishing.

## Troubleshooting

- **Workflow cannot push:** enable read/write workflow permissions; organization policy may override repository settings.
- **Snake image missing:** check that the snake workflow completed and the `output` branch contains the SVG.
- **Metrics placeholder remains:** manually run the metrics workflow and inspect API/rate-limit errors.
- **Spotify says not configured:** check all three secret names and values, then rerun the workflow.
- **Spotify authorization fails:** verify the redirect URI exactly matches `http://127.0.0.1:8888/callback`.

## Security

Never commit Spotify client secrets, refresh tokens, personal access tokens or `.env` files. Rotate credentials immediately if exposed.
