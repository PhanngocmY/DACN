# Phân Quyền Chi Tiết Cho LMS và CTĐT: Keycloak, OPA và Cedar
> **Đồ Án Chuyên Ngành** — So sánh đánh giá 3 bộ thực thi phân quyền (Keycloak, OPA, Cedar) trên cùng tập dữ liệu chuẩn.

---

## 1. Yêu Cầu Môi Trường (NFR-03)
* **Hệ điều hành:** Linux (Ubuntu 22.04+ khuyến nghị)
* **RAM:** $\ge$ 8 GB
* **Công cụ:** Git, Docker Engine, Docker Compose plugin.
*(Không cần cài đặt OPA, Rust/Cargo hay Keycloak ngoài máy chủ host)*.

---

## 2. Khởi Động Nhanh (1-Click Run)

### Bước 1: Tạo tệp phân quyền cho Docker
```bash
printf "UID=%s\nGID=%s\n" "$(id -u)" "$(id -g)" > .env
```

### Bước 2: Khởi chạy cụm dịch vụ
```bash
docker compose up -d --build
```
*Các cổng dịch vụ:*
* **API Gateway (FastAPI):** `http://localhost:8000`
* **OPA Server:** `http://localhost:8181`
* **Keycloak:** `http://localhost:8080` (admin/admin)

### Bước 3: Chạy 15 ca kiểm thử dùng chung (FR-06)
```bash
docker compose exec api python runner/run_cases.py
```
*Kết quả:* In bảng so sánh kết quả của 3 engine với kỳ vọng (5 allow, 10 deny) và lưu báo cáo vào `evidence/ket_qua_kiem_thu.md`.

### Bước 4: Đo độ trễ hiệu năng P95 (FR-08)
```bash
docker compose exec api python runner/benchmark.py
```
*Tham số:* Warm-up 100 lần, lặp chính thức $N = 1000$ lần mỗi engine. Kết quả lưu vào `evidence/ket_qua_do_do_tre_p95.md`.

### Bước 5: Dọn dẹp môi trường
```bash
docker compose down -v
```

---

## 3. Cấu Trúc Thư Mục
* `data/`: Dữ liệu nguồn `data.json`, `cases.yaml`, `cedar_entities.json`.
* `policies/`: 
  * `opa/policy.rego`: Chính sách OPA (4 luật).
  * `cedar/policies.cedar`: Chính sách Cedar DSL.
  * `keycloak/realm-k6-lab.json`: Tệp import Realm duy nhất cho Keycloak.
* `api/`: Mã nguồn FastAPI Gateway, các module adapter kết nối engine, bộ helper sinh reason (NFR-04) và ghi nhật ký (FR-07).
* `runner/`: Kịch bản chạy ca test (`run_cases.py`) và đo độ trễ p95 (`benchmark.py`).
* `evidence/`: Bằng chứng nghiệm thu (FR-01 .. FR-08, `audit.jsonl`, `nghiem_thu.md`).
* `docs/`: Tài liệu đặc tả `thiet_ke.md` và ma trận truy vết `truy_vet.csv`.
