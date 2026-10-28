# Streaming Weather

Monorepo with:

- `cron-data` — Flask API + CLI that fetches weather forecasts from [Open-Meteo](https://open-meteo.com/en/docs)
- `fe` — Preact (Vite) dashboard that calls `GET /api/v1/weather`

## Requirements

| Component | Suggested version |
| --- | --- |
| Python | 3.12+ (Docker image uses `python:3.12-slim`) |
| Node.js | 18+ (LTS recommended) |
| npm | Bundled with Node.js |

No API key is required for Open-Meteo.

## Local overview

The dashboard needs **two processes**:

1. Flask API (`cron-data`) — `http://127.0.0.1:5000`
2. Vite FE (`fe`) — `http://127.0.0.1:5173`

Vite proxies `/api` to Flask, so the FE calls `/api/v1/weather` on the same origin.

```text
Browser → http://127.0.0.1:5173
              │
              ├─ UI (Vite)
              └─ /api/*  ──proxy──►  Flask :5000  ──►  Open-Meteo
```

---

## 1. Backend — `cron-data`

### Setup

**macOS / Linux**

```bash
cd cron-data
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

**Windows (PowerShell)**

```powershell
cd cron-data
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Environment variables (see `.env.example`):

| Variable | Default | Meaning |
| --- | --- | --- |
| `WEATHER_API_HOST` | `127.0.0.1` | Flask bind host |
| `WEATHER_API_PORT` | `5000` | Flask port |

### Run the Flask API (for the FE)

```bash
cd cron-data
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
python run.py
```

Quick check:

```bash
curl http://127.0.0.1:5000/api/v1/weather
```

### Run the CLI to write data files

Flask is not required. The script calls Open-Meteo and writes files under `cron-data/data/`:

```bash
cd cron-data
source .venv/bin/activate
python main.py
```

Output:

- `data/open_meteo.json` — raw response
- `data/current.csv` — current weather
- `data/hourly.csv` — hourly forecast
- `data/daily.csv` — daily forecast

Each run overwrites previous files. CSVs use UTF-8 BOM (Excel-friendly).

### Run tests

```bash
cd cron-data
source .venv/bin/activate
python -m pytest
```

### Docker (API only)

```bash
cd cron-data
docker build -t weather-api .
docker run --rm -p 5000:5000 weather-api
```

The container binds `0.0.0.0:5000` via Gunicorn.

---

## 2. Frontend — `fe`

### Setup

```bash
cd fe
npm install
```

### Run development

**Terminal 1 — API**

```bash
cd cron-data
source .venv/bin/activate
python run.py
```

**Terminal 2 — FE**

```bash
cd fe
npm run dev
```

Open `http://127.0.0.1:5173/`.

### Build + preview

```bash
cd fe
npm run build
npm run preview
```

`vite preview` also proxies `/api` to `http://127.0.0.1:5000` — Flask must still be running.

---

## Quick start checklist

1. [ ] Install Python deps in `cron-data` (venv + `requirements.txt`)
2. [ ] (Optional) Copy `.env.example` → `.env`
3. [ ] Run `python run.py` in `cron-data`
4. [ ] Install npm deps in `fe` (`npm install`)
5. [ ] Run `npm run dev` in `fe`
6. [ ] Open `http://127.0.0.1:5173/`

## Common issues

| Symptom | Cause / fix |
| --- | --- |
| FE fails calling `/api/...` | Flask is not running, or not listening on `:5000` |
| Port 5000 already in use | Change `WEATHER_API_PORT` in `.env` **and** update the proxy target in `fe/middleware/api-proxy.js` |
| venv activate blocked (Windows) | Run `.venv\Scripts\python.exe run.py` directly |
| FE cannot reach Dockerized API | Local FE proxies to `127.0.0.1:5000`; mapping `-p 5000:5000` is usually enough on Mac/Windows |

## Package docs

- [`cron-data/README.md`](cron-data/README.md) — API params, architecture, Docker
- [`fe/README.md`](fe/README.md) — Preact dashboard, Vite proxy
