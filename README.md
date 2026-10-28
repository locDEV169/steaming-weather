# Streaming Weather

Monorepo gồm:

- `cron-data` — Flask API + CLI lấy dự báo thời tiết từ [Open-Meteo](https://open-meteo.com/en/docs)
- `fe` — Dashboard Preact (Vite) gọi API `GET /api/v1/weather`

## Yêu cầu

| Thành phần | Phiên bản gợi ý |
| --- | --- |
| Python | 3.12+ (Docker image dùng `python:3.12-slim`) |
| Node.js | 18+ (khuyến nghị LTS) |
| npm | Đi kèm Node.js |

Không cần API key cho Open-Meteo.

## Tổng quan chạy local

Cần **2 process** khi dùng dashboard:

1. Flask API (`cron-data`) — `http://127.0.0.1:5000`
2. Vite FE (`fe`) — `http://127.0.0.1:5173`

Vite proxy `/api` → Flask, nên FE gọi `/api/v1/weather` cùng origin.

```text
Browser → http://127.0.0.1:5173
              │
              ├─ UI (Vite)
              └─ /api/*  ──proxy──►  Flask :5000  ──►  Open-Meteo
```

---

## 1. Backend — `cron-data`

### Cài đặt

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

Biến môi trường (xem `.env.example`):

| Biến | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `WEATHER_API_HOST` | `127.0.0.1` | Host bind Flask |
| `WEATHER_API_PORT` | `5000` | Port Flask |

### Chạy Flask API (dùng với FE)

```bash
cd cron-data
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
python run.py
```

Kiểm tra nhanh:

```bash
curl http://127.0.0.1:5000/api/v1/weather
```

### Chạy CLI tải dữ liệu ra file

Không cần Flask. Script gọi Open-Meteo rồi ghi vào `cron-data/data/`:

```bash
cd cron-data
source .venv/bin/activate
python main.py
```

Output:

- `data/open_meteo.json` — response thô
- `data/current.csv` — thời tiết hiện tại
- `data/hourly.csv` — theo giờ
- `data/daily.csv` — theo ngày

Mỗi lần chạy ghi đè file cũ. CSV dùng UTF-8 BOM (mở được bằng Excel).

### Chạy test

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

Container bind `0.0.0.0:5000` qua Gunicorn.

---

## 2. Frontend — `fe`

### Cài đặt

```bash
cd fe
npm install
```

### Chạy development

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

Mở `http://127.0.0.1:5173/`.

### Build + preview

```bash
cd fe
npm run build
npm run preview
```

`vite preview` cũng proxy `/api` tới `http://127.0.0.1:5000` — vẫn cần Flask đang chạy.

---

## Checklist khởi động nhanh

1. [ ] Cài Python deps trong `cron-data` (venv + `requirements.txt`)
2. [ ] (Tuỳ chọn) Copy `.env.example` → `.env`
3. [ ] Chạy `python run.py` trong `cron-data`
4. [ ] Cài npm deps trong `fe` (`npm install`)
5. [ ] Chạy `npm run dev` trong `fe`
6. [ ] Mở `http://127.0.0.1:5173/`

## Lỗi thường gặp

| Hiện tượng | Nguyên nhân / cách xử lý |
| --- | --- |
| FE báo lỗi gọi `/api/...` | Flask chưa chạy, hoặc không lắng nghe `:5000` |
| Port 5000 đã dùng | Đổi `WEATHER_API_PORT` trong `.env` **và** cập nhật target proxy trong `fe/middleware/api-proxy.js` |
| Activate venv bị chặn (Windows) | Gọi trực tiếp `.venv\Scripts\python.exe run.py` |
| Docker FE không gọi được API | FE local proxy tới `127.0.0.1:5000`; nếu API trong Docker trên Mac/Windows thường map `-p 5000:5000` là đủ |

## Tài liệu chi tiết theo package

- [`cron-data/README.md`](cron-data/README.md) — API params, architecture, Docker
- [`fe/README.md`](fe/README.md) — Preact dashboard, proxy Vite
