# Weather dashboard (Preact)

Frontend dùng Preact và Vite. Khi load page, dashboard gọi `GET /api/v1/weather` từ Flask API trong `cron-data`. Vite proxy `/api` tới Flask trong cả `npm run dev` và `npm run preview` (cấu hình tại `middleware/api-proxy.js`). Giao diện có chế độ tổng quan, theo giờ và theo ngày, với nhiệt độ, lượng mưa, nhiệt độ cao/thấp và weather code.

## Cài đặt

Từ thư mục `fe/` (project dùng `pnpm-lock.yaml`):

```bash
pnpm install
```

`pnpm-workspace.yaml` bật `allowBuilds.esbuild` và `minimumReleaseAge: 0` để tránh pnpm 11 chặn transitive deps mới publish / chặn postinstall của esbuild.

## Chạy chế độ phát triển

Cần chạy **cả hai** process:

1. Flask API (từ `cron-data/`):

```bash
python run.py
```

Mặc định lắng nghe `http://127.0.0.1:5000`.

2. Vite (từ `fe/`):

```bash
pnpm run dev
```

Mở URL Vite hiển thị trong terminal (thường là `http://127.0.0.1:5173/`). Vite proxy `/api` tới Flask nên FE gọi `/api/v1/weather` cùng origin.

## Build + preview

```bash
pnpm run build
pnpm run preview
```

Build tạo `dist/` cho frontend. `vite preview` cũng proxy `/api` tới `http://127.0.0.1:5000` (cần Flask đang chạy). Hosting production thật (nginx/CDN) vẫn cần reverse proxy riêng nếu không dùng `vite preview`.

Chart.js được bundle qua pnpm. Font DM Sans/Manrope vẫn được tải từ Google Fonts CDN.
