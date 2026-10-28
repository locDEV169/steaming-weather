# Open-Meteo Weather Data

Flask API và CLI lấy dự báo thời tiết từ [Open-Meteo Forecast API](https://open-meteo.com/en/docs). Flask API dùng app factory trong `src/`; package `weather/` giữ trách nhiệm gọi API nguồn, chuyển đổi bảng và lưu file.

## Cấu trúc

```text
cron-data/
├── src/
│   ├── __init__.py                 # Application factory
│   ├── config.py                   # Host/port và Flask settings
│   ├── routes/weather_routes.py    # URL và HTTP method
│   ├── controllers/                # HTTP response/error mapping
│   ├── services/                   # Use cases, gọi package weather
│   └── models/weather.py           # Typed response contract, không dùng ORM
├── tests/                          # Pytest và fixtures
├── weather/                        # Open-Meteo client, transform, storage
├── data/                           # JSON/CSV tạo bởi CLI
├── .env.example                    # Mẫu config local, không chứa secret
├── Dockerfile                      # Container chạy qua Gunicorn
├── main.py                         # Tải dữ liệu và ghi file
├── run.py                          # Chạy Flask development server
└── requirements.txt
```

Chưa có database trong nghiệp vụ hiện tại, nên `src/models/` chỉ khai báo kiểu response; không thêm SQLAlchemy/MongoDB.

## Tham số API

Project dùng các tham số API sau:

- Tọa độ trung tâm Đà Nẵng: latitude `16.0544`, longitude `108.2022`.
- Timezone: `Asia/Bangkok` (GMT+7), cùng múi giờ với Việt Nam.
- Hiện tại: `weather_code`, `temperature_2m`.
- Theo giờ: `temperature_2m`, `weather_code`.
- Theo ngày: `weather_code`, `sunrise`, `rain_sum`, `sunset`, `temperature_2m_max`, `temperature_2m_min`.

API công khai này không cần API key.

## Cài đặt trên Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
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

API cung cấp endpoint `GET /api/v1/weather`. Mỗi request gọi Open-Meteo trực tiếp qua `weather/api.py` và trả payload JSON gồm `current`, `hourly`, `daily` cùng metadata. Endpoint không đọc snapshot từ `data/open_meteo.json` và hiện chưa ghi lại file CSV/JSON.

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

Build và chạy Docker từ thư mục `cron-data`:

```powershell
docker build -t weather-api .
docker run --rm -p 5000:5000 weather-api
```

## Chạy kiểm thử

```powershell
python -m pytest
```

## Chạy local

```
cd cron-data
python -m pip install -r requirements.txt
python run.py
```
