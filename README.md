# ⚡ Sonic the HackHog

**Thread Ripper | The Widowmaker | Fantasma de Luanda**

A self-hosted visitor tracking redirect engine. Accepts any HTTP request, logs the visitor's full metadata (IP, User-Agent, Accept-Language, headers, query params) to SQLite, and immediately returns a `302` redirect — no page content, no interstitial.

```
Visitor → r.ferreirakorp.com → 302 → wise.com
                  ↓
            SQLite log + live terminal
```

## Components

| File | What it does |
|---|---|
| `server.py` | Redirect server — zero dependencies, runs on any Python 3.10+. Logs visits to SQLite, serves an API for the monitor. |
| `monitor.py` | Local terminal monitor — polls the server API and displays visits in a green-on-black hacker terminal with Rich. |
| `docker-compose.yml` | VPS deployment with Cloudflare Tunnel (one command). |

## Quick start

### 1. Deploy on a VPS (Docker)

```bash
# Clone and configure
git clone https://github.com/ferreirakorp/sonic-hackhog.git
cd sonic-hackhog
cp .env.example .env
# Edit .env: set API_KEY, TUNNEL_TOKEN, REDIRECT_URL

# Start
docker compose up -d

# Check logs
docker logs fk-redirect --tail 20
```

### 2. Run the monitor locally (your PC)

```bash
pip install rich requests

# Option A: with .env file
echo "API_KEY=your_key_here" > .env
echo "SERVER_URL=https://r.ferreirakorp.com" >> .env
python monitor.py

# Option B: with arguments
python monitor.py --url https://r.ferreirakorp.com --key YOUR_API_KEY
```

### 3. Run everything locally (no VPS)

```bash
pip install rich requests

# Terminal 1: start the server
export API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
export REDIRECT_URL=https://wise.com/
python server.py

# Terminal 2: start the monitor
python monitor.py --url http://localhost:8099 --key $API_KEY
```

## Configuration

All via environment variables or `.env` file:

| Variable | Default | Description |
|---|---|---|
| `REDIRECT_URL` | `https://wise.com/` | Where visitors get redirected |
| `API_KEY` | *(generated at startup)* | Bearer token for the monitor API |
| `PORT` | `8099` | Server listen port |
| `DB_PATH` | `/opt/redirect/visits.db` | SQLite database path |
| `TUNNEL_TOKEN` | — | Cloudflare Tunnel token (Docker only) |
| `SERVER_URL` | `https://r.ferreirakorp.com` | Monitor: server to poll |
| `POLL_INTERVAL` | `3` | Monitor: seconds between polls |

## API

The server exposes two endpoints (protected by `API_KEY`):

```
GET /api/visits?since=<id>&limit=50
Authorization: Bearer <API_KEY>

→ {"visits": [{"id":1, "ts":"...", "ip":"...", "ua":"...", "lang":"...", "method":"GET", "path":"/", "query":"", "headers":"..."}]}
```

```
GET /api/health

→ {"status":"ok", "total_visits": 42, "ts":"..."}
```

Every other request gets logged and `302`'d to `REDIRECT_URL`.

## Setting up Cloudflare Tunnel

1. Create a tunnel in Cloudflare Zero Trust dashboard (or via API)
2. Configure the tunnel to route `your-domain.com` → `http://redirect:8099`
3. Add a CNAME DNS record: `r.yourdomain.com` → `<tunnel-id>.cfargotunnel.com` (proxied)
4. Put the tunnel token in `.env`

## License

MIT
