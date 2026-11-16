# Tài Liệu Thiết Kế Đầu Vào Dùng Chung & Quy Ước Phân Quyền
**Mã tài liệu:** `docs/thiet_ke.md`  
**Đề tài:** Phân quyền chi tiết cho LMS và CTĐT: Keycloak, OPA và Cedar

---

## 1. Giao Diện API Chuẩn Hóa (`IF-01`)

### Endpoint
* **URI:** `POST /authorize`
* **Content-Type:** `application/json`

### Định dạng Yêu cầu (Request Body)
```json
{
  "subject": "sv_01",
  "action": "view",
  "resource": {
    "type": "course",
    "id": "LMS-ATTT01"
  },
  "engine": "opa"
}
```

* `subject` *(string, bắt buộc)*: Định danh người dùng (`gv_cntt_01`, `gv_toan_01`, `gv_kiem_2khoa`, `sv_01`, `sv_02`, `sv_huy`, hoặc `khach_la`).
* `action` *(string, bắt buộc)*: Hành động (`view` hoặc `edit`).
* `resource` *(object, bắt buộc)*:
  * `type` *(string)*: Loại tài nguyên (`syllabus` hoặc `course`).
  * `id` *(string)*: Mã định danh tài nguyên (`DC-CNTT-001`, `DC-TOAN-001`, `LMS-ATTT01`, `LMS-GT01`).
* `engine` *(string, bắt buộc)*: Bộ thực thi (`opa`, `cedar`, hoặc `keycloak`).

### Định dạng Phản hồi (Response Body)
```json
{
  "decision": "allow",
  "reason": "Hợp lệ / Cho phép truy cập",
  "engine": "opa",
  "latency_ms": 1.25,
  "end_to_end_ms": 3.42
}
```

---

## 2. Quy Ước Ánh Xạ Giữa Các Engine

| Thành phần chung | OPA (Rego input) | Cedar DSL | Keycloak (UMA Ticket) |
|---|---|---|---|
| **Chủ thể (subject)** | `input.subject` $\to$ tra cứu `data.users[input.subject]` | `User::"<subject>"` | Username đăng nhập lấy Access Token |
| **Hành động (action)** | `input.action` (`view` / `edit`) | `Action::"<action>"` | Scope phân quyền (`view` / `edit`) |
| **Loại tài nguyên** | `input.resource.type` (`syllabus` / `course`) | Thực thể PascalCase (`Syllabus` / `Course`) | Resource Type trong Authorization Services |
| **Mã tài nguyên** | `input.resource.id` (`DC-...` / `LMS-...`) | `Syllabus::"<id>"` / `Course::"<id>"` | Tên Resource (`DC-CNTT-001`, `LMS-ATTT01`) |

---

## 3. Quy Ước Lý Do Quyết Định & Bảo Mật Dữ Liệu (`NFR-04`)

Theo yêu cầu **NFR-04** và **HD mục 6.3**, thông báo từ chối quyền truy cập phải mang tính **khách quan, chung chung**, không được làm lộ danh sách hoặc thông tin cá nhân của người khác (PII).

* **Khi được cấp quyền (Allow):**
  * `"Hợp lệ / Cho phép truy cập"`
* **Khi bị từ chối (Deny):**
  * Chủ thể không có trong hệ thống (`khach_la`): `"Chủ thể không tồn tại trong hệ thống"`.
  * Giảng viên thao tác đề cương ngoài khoa chính: `"Khác Khoa quản lý"`.
  * Sinh viên thao tác chỉnh sửa nội dung: `"Không có quyền chỉnh sửa"`.
  * Sinh viên xem khóa học chưa ghi danh: `"Chưa ghi danh vào khóa học"`.
  * Sinh viên đã rút/hủy môn: `"Đã hủy ghi danh khóa học"`.
  * *(Tuyệt đối không liệt kê danh sách sinh viên khác đang học trong lớp).*

---

## 4. Đặc Tả Nhật Ký Kiểm Toán Quyết Định (`DR-04`, `FR-07`)

Mỗi yêu cầu phân quyền gửi đến hệ thống đều được ghi một dòng định dạng JSON Lines (`.jsonl`) vào tệp `evidence/audit.jsonl` gồm 8 trường tiêu chuẩn:

1. `subject`: Mã người dùng yêu cầu.
2. `action`: Hành động yêu cầu (`view` / `edit`).
3. `resource`: Mã tài nguyên thao tác.
4. `decision`: Quyết định (`allow` hoặc `deny`).
5. `reason`: Lý do tóm tắt.
6. `engine`: Tên bộ thực thi (`opa`, `cedar`, `keycloak`).
7. `ts`: Dấu thời gian chuẩn ISO 8601 UTC.
8. `latency_ms`: Thời gian thực thi riêng của engine (ms).

Ví dụ một dòng nhật ký:
```json
{"subject":"sv_01","action":"view","resource":"LMS-ATTT01","decision":"allow","reason":"Hợp lệ / Cho phép truy cập","engine":"opa","ts":"2026-11-13T09:20:00.123456Z","latency_ms":1.15,"end_to_end_ms":2.45}
```
