# Dữ liệu mẫu — SRS-TTTN-K6: Phân quyền chi tiết cho LMS và CTĐT: Keycloak, OPA và Cedar

> Toàn bộ dữ liệu là giả lập, sinh bằng chương trình với hạt giống cố định. Không có người, tổ chức hay hệ thống thật.

## Mục đích

Cung cấp một nguồn dữ liệu duy nhất (người dùng, đề cương hai Khoa, hai khóa học) cùng bảng ca dùng chung và các dạng nạp cho Keycloak, OPA và Cedar, để ba bộ thực thi được so sánh trên cùng đầu vào.

## Danh mục tệp

| Tệp | Nội dung | Phục vụ |
|---|---|---|
| `data.json` | Dữ liệu gốc; nạp vào OPA làm `data` | DR-01..DR-03 |
| `cases.yaml` | 15 ca có kết quả kỳ vọng (gồm ca biên) | FR-01..FR-06, NFR-02 |
| `cedar_entities.json, policies_mau.cedar` | Thực thể và chính sách khởi đầu cho Cedar | IF-04 |
| `realm-k6-lab.json` | Realm Keycloak lab: 6 tài khoản, thuộc tính khoa, client bật Authorization | IF-02 |

## Cách sử dụng

1. Keycloak: `kc.sh start-dev --import-realm` với realm-k6-lab.json đặt trong /opt/keycloak/data/import; tạo resource/scope/policy theo thiết kế của nhóm.
2. OPA: `opa run --server data.json policy.rego`; gửi input từ cases.yaml.
3. Cedar: `cedar authorize --policies policies_mau.cedar --entities cedar_entities.json --principal 'User::"sv_01"' --action 'Action::"view"' --resource 'Course::"LMS-ATTT01"'` [CẦN KIỂM CHỨNG cú pháp CLI theo phiên bản].
4. Bộ chạy ca đọc cases.yaml, gọi ba engine, in bảng khớp/lệch; đo độ trễ trên chính bộ ca này lặp N lần.

## Kết quả mong đợi (đáp án để kiểm thử)

| Kiểm tra | Kết quả mong đợi |
|---|---|
| Tổng số ca | 15 (5 allow, 10 deny) |
| Ba engine trên cases.yaml | Cùng kết quả ở mọi ca (FR-06); ca lệch phải ghi nguyên nhân |
| CT06 (GV kiêm 2 khoa) | deny theo quy tắc mẫu — nhóm xác nhận quy tắc với GV |
| LM09 (chủ thể lạ) | deny ở cả ba (mặc định từ chối) |

## Lưu ý

- Mật khẩu và secret trong realm chỉ dùng cho lab, đổi nếu lab dùng chung mạng.
- Chính sách Cedar mẫu chưa xử lý ca CT06/khoa_phu — đó là chỗ để nhóm thiết kế.

## Sinh lại dữ liệu

`python gen_data.py <thư mục đầu ra>` trong thư mục `_build` — cùng hạt giống cho cùng kết quả.
