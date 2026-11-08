# Sonic the HackHog

**Thread Ripper | The Widowmaker | Fantasma de Luanda**

A visitor tracking redirect engine with two deployment modes: a full **VPS setup** (Python + Docker + Cloudflare Tunnel) with a live terminal monitor, and a zero-infra **Cloudflare Pages** setup with auto-updating OG link previews. Both log visitor metadata and instantly 302 redirect.

```
                    ┌─── Option A: VPS ───────────────────────┐
                    │ Visitor → your-domain.com → 302 → target│
                    │               ↓                         │
                    │         SQLite + live terminal           │
                    └─────────────────────────────────────────┘

                    ┌─── Option B: Cloudflare Pages ──────────┐
                    │ Visitor → something.pages.dev → 302     │
                    │               ↓                         │
                    │     Cloudflare logs + daily OG update    │
                    └─────────────────────────────────────────┘
```

---

## Option A: VPS Deployment (Docker)

Full self-hosted setup with SQLite logging, API, and a live hacker terminal monitor.

### Components

| File | What it does |
|---|---|
| `server.py` | Redirect server — zero Python dependencies, runs on 3.10+. Logs visits to SQLite, serves an API for the monitor. |
| `monitor.py` | Local terminal monitor — polls the server API and displays visits in a green-on-black hacker terminal (Rich). |
| `docker-compose.yml` | VPS deployment with Cloudflare Tunnel (one command). |

### Quick start

```bash
git clone https://github.com/ferreirakorp/sonic-hackhog.git
cd sonic-hackhog

# Configure
cp .env.example .env
# Edit .env: set API_KEY, TUNNEL_TOKEN, REDIRECT_URL

# Deploy
docker compose up -d

# Check
docker logs fk-redirect --tail 20
```

### Run the monitor (your PC)

```bash
pip install rich requests

# Option A: .env file
cat > .env <<EOF
API_KEY=your_key_here
SERVER_URL=https://your-redirect-domain.com
POLL_INTERVAL=3
EOF
python monitor.py

# Option B: CLI args
python monitor.py --url https://your-redirect-domain.com --key YOUR_API_KEY
```

### Run everything locally (no VPS)

```bash
pip install rich requests

# Terminal 1: server
export API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export REDIRECT_URL=https://wise.com/
python server.py

# Terminal 2: monitor
python monitor.py --url http://localhost:8099 --key $API_KEY
```

### VPS Configuration

| Variable | Default | Description |
|---|---|---|
| `REDIRECT_URL` | `https://wise.com/` | Where visitors get redirected |
| `API_KEY` | *(auto-generated)* | Bearer token for the monitor API |
| `PORT` | `8099` | Server listen port |
| `DB_PATH` | `/opt/redirect/visits.db` | SQLite database path |
| `TUNNEL_TOKEN` | — | Cloudflare Tunnel token (Docker only) |
| `SERVER_URL` | `https://r.ferreirakorp.com` | Monitor: server to poll |
| `POLL_INTERVAL` | `3` | Monitor: seconds between polls |

### API

```
GET /api/visits?since=<id>&limit=50
Authorization: Bearer <API_KEY>
→ {"visits": [{"id":1, "ts":"...", "ip":"...", "ua":"...", ...}]}

GET /api/health
→ {"status":"ok", "total_visits": 42, "ts":"..."}
```

Every other request gets logged and `302`'d to `REDIRECT_URL`.

### Cloudflare Tunnel setup

1. Create a tunnel in Cloudflare Zero Trust dashboard (or via API/CLI)
2. Configure the tunnel to route your domain → `http://redirect:8099`
3. Add a CNAME DNS record: `r.yourdomain.com` → `<tunnel-id>.cfargotunnel.com` (proxied)
4. Put the tunnel token in `.env`

---

## Option B: Cloudflare Pages (Zero Infra)

A serverless redirect on a free `*.pages.dev` URL. No VPS, no domain, no Docker. Runs entirely on Cloudflare's edge. Includes an auto-updating OG title that refreshes once per day with a timestamp.

### How it works

1. Visitor opens the `*.pages.dev` link (any path works)
2. Cloudflare Pages Function runs at the edge:
   - Logs visitor metadata (IP, UA, language, referer, method, path)
   - Generates or retrieves today's OG timestamp from KV
   - Serves HTML with OG meta tags → link previews show `Comprovativo_DDMMYYYYHHMM`
   - Instantly redirects to the target URL (meta refresh + JS)
3. The OG title updates once per day — the first request of the day locks a fresh timestamp in Cloudflare KV, and every subsequent request that day serves the same value

### Files

```
cf-pages/
├── functions/
│   └── [[path]].js          # Edge function — handles all routes
├── public/
│   └── _headers              # Tells search engines not to index
└── wrangler.toml.example     # Template config (copy to wrangler.toml)
```

### Deploy (step by step)

**Prerequisites:** Node.js 18+, a free Cloudflare account.

```bash
# 1. Install wrangler
npm install -g wrangler

# 2. Login to Cloudflare
wrangler login
# Or set env vars instead:
# export CLOUDFLARE_API_TOKEN=your_token
# export CLOUDFLARE_ACCOUNT_ID=your_account_id

# 3. Clone and enter the Pages directory
git clone https://github.com/ferreirakorp/sonic-hackhog.git
cd sonic-hackhog/cf-pages

# 4. Create the KV namespace (for daily OG persistence)
npx wrangler kv namespace create OG_STATE
# Note the namespace ID from the output

# 5. Create config
cp wrangler.toml.example wrangler.toml
# Edit wrangler.toml: replace YOUR_KV_NAMESPACE_ID with the ID from step 4

# 6. Create the Pages project
npx wrangler pages project create sonic-redirect --production-branch main

# 7. Deploy
npx wrangler pages deploy public --project-name sonic-redirect
```

Your link is live at: `https://sonic-redirect.pages.dev/`

### Change the redirect target

Set the `REDIRECT_URL` environment variable in the Cloudflare dashboard:

1. Go to **Workers & Pages** → your project → **Settings** → **Environment variables**
2. Add `REDIRECT_URL` = `https://your-target.com/`
3. Redeploy

Or pass it in `wrangler.toml`:

```toml
[vars]
REDIRECT_URL = "https://your-target.com/"
```

### View live logs

```bash
npx wrangler pages deployment tail --project-name sonic-redirect
```

Every visitor hit appears as JSON:

```json
{"ts":"2026-11-08T15:33:12.000Z","ip":"102.xx.xx.xx","ua":"Mozilla/5.0...","lang":"pt-AO","method":"GET","path":"/"}
```

When the OG title updates (first request of a new day):

```json
{"event":"OG_DAILY_UPDATE","date":"2026-11-09","new_og":"Comprovativo_091120260742","generated_at":"2026-11-09T06:42:18.000Z"}
```

### OG auto-update explained

The link preview title follows the format `Comprovativo_DDMMYYYYHHMM`:

- **DD** — day (WAT timezone, UTC+1)
- **MM** — month
- **YYYY** — year
- **HH** — hour when the daily update happened
- **MM** — minute when the daily update happened

The timestamp is generated once per day by the first visitor and stored in Cloudflare KV with a 48-hour TTL. All subsequent requests that day serve the same cached value. At midnight WAT, the next visitor triggers a new generation.

Without KV configured, it falls back to computing the timestamp on every request (still works, but the time portion may vary between requests).

### Pages Configuration

| Setting | Default | Description |
|---|---|---|
| `REDIRECT_URL` | `https://wise.com/` | Where visitors get redirected |
| `OG_STATE` (KV) | — | KV namespace binding for daily OG persistence |

---

## License

MIT — see [LICENSE](LICENSE).
