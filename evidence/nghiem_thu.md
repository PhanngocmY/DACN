# Bảng Nghiệm Thu Đồ Án (HD Mục 11)
## So Sánh Phân Quyền Chi Tiết: Keycloak, OPA và Cedar

| STT | Tiêu chí nghiệm thu | Yêu cầu | Tệp / Bằng chứng kiểm tra | Trạng thái |
|---|---|---|---|---|
| 1 | Môi trường tái lập sạch | NFR-03 | `docker-compose.yml`, `README.md` | Sẵn sàng kiểm tra |
| 2 | Bộ ca dùng chung duy nhất | NFR-02 | `data/cases.yaml` (15 ca) | Đã chuẩn hóa |
| 3 | Bảo mật thông tin lab | NFR-01 | Secret lab giả lập, không trỏ hệ thống thật | Đã tuân thủ |
| 4 | Không rò rỉ dữ liệu khi từ chối | NFR-04 | `api/reason_helper.py`, `docs/thiet_ke.md` | Đã chuẩn hóa |
| 5 | Giao diện API quyết định thống nhất | IF-01 | `api/main.py` (`POST /authorize`) | Hoàn thành |
| 6 | Phân quyền đề cương theo Khoa | FR-01, FR-02 | Ca CT01 - CT06 | Sẵn sàng chạy |
| 7 | Phân quyền khóa học & ghi danh | FR-03, FR-04, FR-05 | Ca LM01 - LM09 | Sẵn sàng chạy |
| 8 | Tính nhất quán giữa 3 engine | FR-06 | 15 ca khớp kỳ vọng (5 allow, 10 deny) | Sẵn sàng chạy |
| 9 | Nhật ký kiểm toán 8 trường chuẩn | FR-07, DR-04 | `evidence/audit.jsonl` (đủ 45 dòng cho 15 ca x 3) | Sẵn sàng chạy |
| 10 | Đo độ trễ p95 công bằng | FR-08 | `runner/benchmark.py` (Warm-up 100, N=1000) | Sẵn sàng chạy |
| 11 | Ma trận truy vết yêu cầu | HD mục 11 | `docs/truy_vet.csv` | Hoàn thành |
