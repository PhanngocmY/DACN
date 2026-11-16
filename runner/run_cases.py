import os
import sys
import argparse
import yaml
import httpx
from tabulate import tabulate

def load_cases(cases_path: str):
    if not os.path.exists(cases_path):
        raise FileNotFoundError(f"Không tìm thấy file ca kiểm thử tại: {cases_path}")
    with open(cases_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("cases", [])

def main():
    parser = argparse.ArgumentParser(description="Chạy bộ 15 ca kiểm thử phân quyền so sánh các engine")
    parser.add_argument("--api-url", default=os.getenv("API_URL", "http://localhost:8000"), help="URL của Decision API")
    parser.add_argument("--cases-file", default=os.getenv("CASES_FILE", "/app/data/cases.yaml"), help="Đường dẫn file cases.yaml")
    parser.add_argument("--engines", default="opa,cedar,keycloak", help="Danh sách engine cần chạy (phân cách bằng dấu phẩy)")
    parser.add_argument("--out-evidence", default="/app/evidence/ket_qua_kiem_thu.md", help="File xuất kết quả nghiệm thu")
    args = parser.parse_args()

    # Fallback đường dẫn nếu chạy ngoài host
    if not os.path.exists(args.cases_file) and os.path.exists("data/cases.yaml"):
        args.cases_file = "data/cases.yaml"

    cases = load_cases(args.cases_file)
    engines = [e.strip() for e in args.engines.split(",") if e.strip()]

    print(f"\n=======================================================")
    print(f"🚀 BẮT ĐẦU CHẠY KIỂM THỬ PHÂN QUYỀN (15 CA)")
    print(f"📡 API Gateway: {args.api_url}")
    print(f"⚙️  Engines: {', '.join(engines)}")
    print(f"📄 Tập ca: {args.cases_file} ({len(cases)} ca)")
    print(f"=======================================================\n")

    client = httpx.Client(timeout=10.0)

    # Kiểm tra API sống
    try:
        resp = client.get(f"{args.api_url}/health")
        if resp.status_code != 200:
            print(f"❌ API Gateway không phản hồi tốt: {resp.status_code}")
    except Exception as e:
        print(f"❌ Không thể kết nối tới API tại {args.api_url}: {e}")
        sys.exit(1)

    table_data = []
    headers = ["CaID", "Yêu cầu", "Subject", "Action", "Resource", "Kỳ vọng"] + [e.upper() for e in engines] + ["Trạng thái"]

    total_matched = 0
    engine_stats = {e: {"allow": 0, "deny": 0, "match": 0} for e in engines}

    for c in cases:
        case_id = c["id"]
        yeu_cau = c.get("yeu_cau", "")
        subject = c["subject"]
        action = c["action"]
        res = c["resource"]
        res_display = f"{res.get('type')}:{res.get('id')}"
        expected = c["expected"]

        row = [case_id, yeu_cau, subject, action, res_display, expected]
        case_matched = True

        for e in engines:
            payload = {
                "subject": subject,
                "action": action,
                "resource": {
                    "type": res.get("type"),
                    "id": res.get("id")
                },
                "engine": e
            }

            try:
                r = client.post(f"{args.api_url}/authorize", json=payload)
                if r.status_code == 200:
                    dec = r.json().get("decision", "error")
                else:
                    dec = f"err_{r.status_code}"
            except Exception as ex:
                dec = "conn_err"

            row.append(dec)

            # Thống kê
            if dec == "allow":
                engine_stats[e]["allow"] += 1
            elif dec == "deny":
                engine_stats[e]["deny"] += 1

            if dec == expected:
                engine_stats[e]["match"] += 1
            else:
                case_matched = False

        status_icon = "✅ KHỚP" if case_matched else "❌ LỆCH"
        if case_matched:
            total_matched += 1
        row.append(status_icon)
        table_data.append(row)

    # In bảng ra console
    rendered_table = tabulate(table_data, headers=headers, tablefmt="grid")
    print(rendered_table)

    print("\n---------------- TỔNG HỢP KẾT QUẢ ----------------")
    for e in engines:
        st = engine_stats[e]
        print(f"🔹 {e.upper()}: Allow = {st['allow']} | Deny = {st['deny']} | Khớp kỳ vọng = {st['match']}/{len(cases)}")
    print(f"🎯 Tổng số ca khớp toàn diện cả {len(engines)} engine: {total_matched}/{len(cases)}")
    print("---------------------------------------------------\n")

    # Lưu bằng chứng ra file markdown
    try:
        os.makedirs(os.path.dirname(args.out_evidence), exist_ok=True)
        with open(args.out_evidence, "w", encoding="utf-8") as f:
            f.write("# Báo Cáo Kết Quả Kiểm Thử 15 Ca Dùng Chung\n\n")
            f.write(f"- Ngày chạy: `{os.popen('date').read().strip()}`\n")
            f.write(f"- Tổng số ca khớp toàn diện: **{total_matched}/{len(cases)}**\n\n")
            f.write("```\n" + rendered_table + "\n```\n\n")
            f.write("## Thống Kê Từng Engine\n\n")
            for e in engines:
                st = engine_stats[e]
                f.write(f"- **{e.upper()}**: Allow: {st['allow']}, Deny: {st['deny']}, Khớp kỳ vọng: {st['match']}/{len(cases)}\n")
        print(f"💾 Đã lưu kết quả nghiệm thu vào: {args.out_evidence}")
    except Exception as e:
        print(f"⚠️ Không thể ghi file {args.out_evidence}: {e}")

if __name__ == "__main__":
    main()
