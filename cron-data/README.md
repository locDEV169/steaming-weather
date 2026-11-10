# Open-Meteo Weather Data

Flask API và CLI lấy dự báo thời tiết từ [Open-Meteo Forecast API](https://open-meteo.com/en/docs). Flask dùng app factory trong `app/`; feature weather nằm vertical slice dưới `app/modules/weather/`.

## Cấu trúc

Tên folder `cron-data` là lịch sử monorepo; hiện tại đây là **Flask weather API + CLI**, kèm ingest lên Supabase. Scheduler Docker (sidecar) gọi `POST /api/v1/current-weather`.

```text
cron-data/
├── app/                              # Flask application package
│   ├── __init__.py                   # Application factory (create_app)
│   ├── config.py                     # Host/port, CORS, API key, Supabase env
│   ├── common/                       # CORS, logging, errors, optional auth
│   ├── openapi/                      # Shared OpenAPI sources (root + components)
│   ├── static/swagger.json           # Assembled OpenAPI cho /api/docs (do not edit by hand)
│   └── modules/
│       └── weather/                  # Weather module
│           ├── __init__.py           # Export blueprint
│           ├── openapi/              # Module OpenAPI paths + schemas
│           ├── routes/               # URL + HTTP method
│           ├── controllers/          # HTTP response/error mapping
│           ├── services/             # Use cases: forecast, rainny, AQ, ingest
│           ├── repositories/         # Supabase PostgREST upsert/read
│           ├── models/               # Typed response contract (không ORM)
│           └── provider/             # Open-Meteo client + CLI export
│               ├── api.py / air_quality.py
│               ├── config.py / transform.py
│               └── storage.py
├── supabase/migrations/              # SQL schema (local migrate hoặc SQL Editor)
├── scripts/migrate.py                # Apply SQL qua psql + DATABASE_URL
├── scripts/assemble_openapi.py       # Merge OpenAPI fragments → static/swagger.json
├── tests/                            # Pytest
├── data/                             # JSON/CSV tạo bởi CLI (gitignore)
├── .env.example
├── Dockerfile                        # COPY app; Gunicorn (env via --env-file / compose)
├── Dockerfile.cron                   # Alpine + curl + crond sidecar
├── docker-compose.yml                # weather-api + current-weather-cron
├── scripts/cron_current_weather.sh   # POST current-weather per location
├── scripts/docker_cron_entrypoint.sh # Install crontab from env, run crond
├── main.py                           # CLI tải dữ liệu và ghi file
├── run.py                            # Flask development server
└── requirements.txt
```

### Vai trò từng phần

| Phần | Việc |
| --- | --- |
| `app/` | Factory + config + static |
| `app/common/` | Cross-cutting HTTP middleware |
| `app/openapi/` | Shared OpenAPI root (`info`/`servers`) + `securitySchemes` / `ApiErrorResponse` |
| `app/modules/<name>/openapi/` | Paths (+ optional schemas) của module; source of truth khi sửa docs |
| `app/static/swagger.json` | Artifact assemble; Swagger UI đọc file này |
| `app/modules/weather/` | routes → controllers → services → repositories |
| `app/modules/weather/provider/` | Gọi Open-Meteo, transform, lưu file CLI |
| `supabase/` | Migration SQL: `weather_snapshots` (latest-only) và `lifestyle_insights` (append-only) |
| `scripts/migrate.py` | Apply migration từ local (`psql` + `DATABASE_URL`) |
| `scripts/assemble_openapi.py` | Ghép fragments → `app/static/swagger.json` |
| `tests/` | Pytest cho API, domain, ingest |
| `app/modules/weather/models/` | TypedDict / contract response; **không** SQLAlchemy |

### OpenAPI (multi-module)

Sửa docs ở fragment, rồi assemble (từ `cron-data/`):

```powershell
python scripts/assemble_openapi.py
```

Thêm module mới: tạo `app/modules/<name>/openapi/paths.json` (+ `schemas.json` nếu cần) → chạy assemble → commit cả fragments và `app/static/swagger.json`. Không sửa tay file static khi đã có fragment.

Snapshot Supabase là persistence tùy chọn qua `POST /api/v1/ingest`. GET live vẫn gọi Open-Meteo trực tiếp và không đọc `data/` hay DB.

## Tham số API

Project dùng các tham số API sau:

- Tọa độ trung tâm Đà Nẵng: latitude `16.0544`, longitude `108.2022`.
- Timezone: `Asia/Bangkok` (GMT+7), cùng múi giờ với Việt Nam.
- Cửa sổ thời gian: `past_days=7`, `forecast_days=7` (7 ngày quá khứ dạng archived forecast + 7 ngày dự báo).
- Hiện tại: `weather_code`, `temperature_2m`, `relative_humidity_2m`, `is_day`, `apparent_temperature`, `precipitation`, `rain`, `showers`, `wind_speed_10m`, `wind_gusts_10m`.
- Theo giờ: `temperature_2m`, `weather_code`, `precipitation_probability`, `precipitation`, `rain`, `showers`, `wind_speed_10m`, `wind_gusts_10m`, `uv_index`.
- Theo ngày: `weather_code`, `sunrise`, `rain_sum`, `precipitation_sum`, `precipitation_probability_max`, `sunset`, `temperature_2m_max`, `temperature_2m_min`, `wind_speed_10m_max`, `wind_gusts_10m_max`.

API nguồn Open-Meteo không cần API key. Auth cho Flask API là **optional** (xem middleware bên dưới).

## Middleware

`app/common/` đăng ký trong app factory:

| Middleware | Hành vi |
| --- | --- |
| CORS | Header CORS + preflight `OPTIONS`. `CORS_ORIGINS=*` (mặc định) hoặc danh sách origin cách nhau bởi dấu phẩy. |
| Request logging | Log `METHOD path -> status (duration_ms)` qua logger `weather.api`. |
| Global errors | JSON `{"error":{"code","message"}}` cho 404/405 và exception chưa bắt (`INTERNAL_ERROR`, không lộ chi tiết nội bộ). Upstream 502/504 vẫn map ở controller. |
| Optional auth | Nếu `WEATHER_API_KEY` trống/không set → không bắt auth. Nếu có giá trị → `/api/v1/*` yêu cầu `X-API-Key` hoặc `Authorization: Bearer <key>`. Swagger/static không bị chặn. |

Ví dụ bật auth:

```powershell
$env:WEATHER_API_KEY="change-me"
python run.py
# Invoke-RestMethod http://127.0.0.1:5000/api/v1/weather -Headers @{ "X-API-Key" = "change-me" }
```

## Cài đặt trên Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
```
cd cron-data
source .venv/Scripts/activate   # nếu chưa có venv trong cron-data:
# python -m venv .venv && source .venv/Scripts/activate
python -m pip install -r requirements.txt
python run.py
```


Có thể tạo `.env` local từ `.env.example`; file `.env` được Git bỏ qua.

Nếu PowerShell chặn activate script, có thể gọi Python trong virtual environment trực tiếp:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Chạy

```powershell
python main.py
```

Project tạo thư mục `data/` gồm:

- `open_meteo.json`: response nguyên bản, gồm metadata và đơn vị do API trả về.
- `current.csv`: một dòng dữ liệu hiện tại.
- `hourly.csv`: một dòng trên mỗi mốc thời gian theo giờ.
- `daily.csv`: một dòng trên mỗi ngày dự báo.

CSV dùng UTF-8 BOM để mở thuận tiện bằng Excel. Mỗi lần chạy sẽ ghi đè các file đầu ra trước đó. Lỗi kết nối, HTTP hoặc response không hợp lệ sẽ được báo trên terminal.

## HTTP API cho backend

API cung cấp:

- `GET /api/v1/weather` — mỗi request gọi Open-Meteo trực tiếp qua `app/modules/weather/provider/api.py` và trả payload JSON gồm `current`, `hourly`, `daily` cùng metadata. Endpoint không đọc snapshot từ `data/open_meteo.json` và hiện chưa ghi lại file CSV/JSON.
- `GET /api/v1/weather-rainny-forecast` — series lượng mưa theo ngày (past + current + future) để FE chart. Không cần query param; server lấy `as_of` theo `Asia/Bangkok`. Mỗi phần tử có `date`, `rain_sum`, và `kind` (`past` | `current` | `future`).
- `GET /api/v1/air-quality` — mỗi request gọi Open-Meteo Air Quality API và trả payload upstream (European AQI + pollutants hiện tại cho Đà Nẵng) kèm `results.overall` (band từ `european_aqi`, bảng Open-Meteo/EEA 2024) và `results.summary` (nhãn/ý nghĩa song ngữ VI+EN để FE hiển thị). `hourly.uv_index` được giữ trong payload để ingest lưu lên Supabase. Khi có `uv_index`, `results.uv` là mức WHO của giờ hiện tại (0–2 Thấp, 3–5 Trung bình, 6–7 Cao, 8–10 Rất cao, ≥11 Cực cao). Không dùng US AQI; chưa có đánh giá từng pollutant. Text summary mang tính thông tin UI, không phải tư vấn y tế.
- `POST /api/v1/ingest` — fetch + shape weather/rainny/air_quality rồi upsert vào Supabase (`weather_snapshots`). Không ghi `lifestyle_insights`. Cần `WEATHER_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`. Cron chưa gắn; gọi tay để seed. Partial update từng kind được phép.
- `POST /api/v1/lifestyle-insights` — API riêng: fetch Open-Meteo, cắt 72 giờ (nhiệt độ, mã thời tiết, mưa, gió, `apparent_temperature`) và **insert** một dòng vào `lifestyle_insights`. Nhãn giờ của dòng mới là UTC. Mỗi giờ lưu `apparent_temperature` của đúng giờ đó. `current` vẫn kèm giá trị này khi Open-Meteo trả về. Không gọi `run_ingest()` và không ghi `weather_snapshots`. Cần cùng `WEATHER_API_KEY` và Supabase service role.
- `GET /api/v1/lifestyle-insights` — đọc dòng `lifestyle_insights` có `fetched_at` mới nhất. Phơi đồ và rửa xe dùng 3 giờ đầu từ `as_of`. Giờ nào có xác suất mưa ≥ 40% hoặc `precipitation` ≥ 0.2 mm thì có `flag` "Nguy cơ ướt". Điểm phơi đồ = 100 trừ trung bình PoP của 3 giờ đó (null tính là 0). `laundry.message` là câu của dòng quy chuẩn khớp điểm. `car_wash.mean` là cùng trung bình PoP. Mean nằm trong `score_min` và `score_max` của một mức thì `car_wash.message` là câu của mức đó. `score_min` null được tính là 0. Không trả điểm tập luyện. Không gọi Open-Meteo.
- `GET /api/v1/snapshots/{weather|rainny|air-quality}` — đọc snapshot đã ingest từ Supabase và trả **payload** (cùng shape với live GET tương ứng). Không gọi Open-Meteo. 404 nếu chưa có row; cần `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`.

### Seed data lên Supabase (no-cron MVP)

1. Tạo project Supabase; copy **Project URL**, **anon** (cho FE sau), **service_role** (chỉ Flask).
2. Apply schema `weather_snapshots` từ local (cần [psql](https://www.postgresql.org/download/) trên PATH):

```powershell
# Dashboard → Project Settings → Database → URI → dán vào DATABASE_URL trong .env
# (đây là Postgres connection string, không phải service_role JWT)
cd cron-data
python scripts/migrate.py
```

Fallback nếu chưa có `psql`: mở **SQL Editor** trên Dashboard và chạy `supabase/migrations/001_weather_snapshots.sql`, rồi `002_lifestyle_insights.sql`.

`002` tạo bảng lịch sử `lifestyle_insights`. Chạy riêng:

```powershell
python scripts/migrate.py supabase/migrations/002_lifestyle_insights.sql
```

3. Điền `cron-data/.env` (xem `.env.example`) — **không commit** service role / `DATABASE_URL`.
4. Chạy Flask rồi ingest:

```powershell
$env:WEATHER_API_KEY="your-local-key"
# hoặc set trong .env rồi:
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/v1/ingest -Headers @{ "X-API-Key" = "your-local-key" }
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/v1/lifestyle-insights -Headers @{ "X-API-Key" = "your-local-key" }
```

```bash
curl -X POST http://127.0.0.1:5000/api/v1/ingest -H "X-API-Key: your-local-key"
```

Đọc snapshot sau khi ingest (không cần API key nếu `WEATHER_API_KEY` trống):

```bash
curl http://127.0.0.1:5000/api/v1/snapshots/weather
curl http://127.0.0.1:5000/api/v1/snapshots/rainny
curl http://127.0.0.1:5000/api/v1/snapshots/air-quality
```

Chạy development server trong thư mục `cron-data`:

```powershell
python run.py
```

Mặc định server chỉ bind `127.0.0.1:5000`. Backend chạy ở process khác trên cùng máy có thể gọi `http://127.0.0.1:5000/api/v1/weather`. Nếu backend chạy ở container/máy khác, cấu hình `WEATHER_API_HOST=0.0.0.0` và `WEATHER_API_PORT=5000`, sau đó giới hạn truy cập bằng firewall/private network hoặc bổ sung authentication trước khi expose ra ngoài.

Ví dụ kiểm tra:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/v1/weather
```

Lỗi upstream trả JSON theo dạng `{"error":{"code":"...","message":"..."}}`: timeout là HTTP `504`; lỗi kết nối/HTTP upstream hoặc response không hợp lệ là HTTP `502`. Request gọi live không có cache, nên thời gian và khả năng đáp ứng phụ thuộc Open-Meteo.

Production nên chạy qua WSGI server thay vì Flask development server; khi container hóa, bind service vào `0.0.0.0` và giới hạn truy cập ở network layer.

Build và chạy Docker từ thư mục `cron-data` (cần `.env` từ `.env.example` — Supabase/API key/Telegram không được bake vào image):

```powershell
docker compose up --build
```

Compose chạy hai service:

| Service | Việc |
| --- | --- |
| `weather-api` | Gunicorn API (port host `${WEATHER_API_PORT:-7500}`) |
| `current-weather-cron` | `crond` sidecar: `POST /api/v1/current-weather` theo lịch |

Cron defaults (override trong `.env`):

- `CURRENT_WEATHER_CRON_SCHEDULE=0 * * * *` (mỗi giờ)
- `CURRENT_WEATHER_CRON_LOCATIONS=da_nang,sai_gon`
- `WEATHER_API_KEY` phải khớp key của API

Chạy tay một vòng (trong container cron hoặc host có `curl`):

```powershell
docker compose exec current-weather-cron /usr/local/bin/cron_current_weather.sh
```

Hoặc chỉ build API (không cron):

```powershell
docker build -t weather-api .
docker run --rm -p 5000:5000 --env-file .env -e WEATHER_API_HOST=0.0.0.0 weather-api
```

`-e WEATHER_API_HOST=0.0.0.0` bắt buộc nếu `.env` local đang set `127.0.0.1` (tránh container chỉ listen localhost).

## Chạy kiểm thử

```powershell
python -m pytest
```

## Chạy local

### on window
```
cd cron-data
python -m pip install -r requirements.txt
python run.py
```

OR

```
.venv/Scripts/python.exe run.py
```


### on mac
```
python3 -m venv path/to/venv
source path/to/venv/bin/activate
python3 -m pip install -r requirements.txt
python3 run.py
```


## Noted: 
```bash
export PATH="/c/Program Files/PostgreSQL/18/bin:$PATH"
psql --version
```