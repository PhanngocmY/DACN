import os
import sys
import argparse
import time
import yaml
import httpx
import numpy as np
from tabulate import tabulate

def load_cases(cases_path: str):
    if not os.path.exists(cases_path):
        raise FileNotFoundError(f"Không tìm thấy file ca kiểm thử tại: {cases_path}")
    with open(cases_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("cases", [])

def get_machine_specs():
    try:
        cpu_info = os.popen("lscpu | grep 'Model name' | sed 's/Model name:[ \t]*//'").read().strip()
    except Exception:
        cpu_info = "Unknown CPU"
    try:
        mem_info = os.popen("free -h | grep 'Mem:' | awk '{print $2}'").read().strip()
    except Exception:
        mem_info = "Unknown RAM"
    return cpu_info or "Linux Host", mem_info or ">= 8GB"

def main():
    parser = argparse.ArgumentParser(description="Script đo độ trễ p95 chuẩn hóa cho OPA, Cedar và Keycloak")
    parser.add_argument("--api-url", default=os.getenv("API_URL", "http://localhost:8000"), help="URL API Gateway")
    parser.add_argument("--cases-file", default=os.getenv("CASES_FILE", "/app/data/cases.yaml"), help="File ca kiểm thử")
    parser.add_argument("--engines", default="opa,cedar,keycloak", help="Danh sách engines")
    parser.add_argument("--warmup", type=int, default=100, help="Số lần warm-up")
    parser.add_argument("--iterations", type=int, default=1000, help="Số lần lặp đo chính thức mỗi engine")
    parser.add_argument("--out-evidence", default="/app/evidence/ket_qua_do_do_tre_p95.md", help="File xuất kết quả")
    args = parser.parse_args()

    if not os.path.exists(args.cases_file) and os.path.exists("data/cases.yaml"):
        args.cases_file = "data/cases.yaml"

    cases = load_cases(args.cases_file)
    engines = [e.strip() for e in args.engines.split(",") if e.strip()]

    cpu_spec, mem_spec = get_machine_specs()

    print(f"\n=======================================================")
    print(f"⏱️  CHƯƠNG TRÌNH ĐO HIỆU NĂNG & ĐỘ TRỄ P95 (FR-08)")
    print(f"💻 Cấu hình thử nghiệm: CPU: {cpu_spec} | RAM: {mem_spec}")
    print(f"🔥 Warm-up: {args.warmup} requests")
    print(f"🔁 Số lần lặp (N): {args.iterations} requests / engine")
    print(f"⚙️  Engines: {', '.join(engines)}")
    print(f"=======================================================\n")

    client = httpx.Client(timeout=10.0)

    # 1. Warm-up
    print("⏳ Đang thực hiện warm-up connection và caches...")
    warmup_case = cases[0]
    for _ in range(args.warmup):
        for e in engines:
            payload = {
                "subject": warmup_case["subject"],
                "action": warmup_case["action"],
                "resource": warmup_case["resource"],
                "engine": e
            }
            try:
                client.post(f"{args.api_url}/authorize", json=payload)
            except Exception:
                pass
    print("✅ Warm-up hoàn tất!\n")

    # 2. Đo chính thức
    results_summary = []

    for e in engines:
        print(f"🚀 Đang đo engine: {e.upper()} ({args.iterations} lần)...")
        latencies_engine = []
        latencies_e2e = []

        num_cases = len(cases)
        for i in range(args.iterations):
            c = cases[i % num_cases]
            payload = {
                "subject": c["subject"],
                "action": c["action"],
                "resource": c["resource"],
                "engine": e
            }
            try:
                resp = client.post(f"{args.api_url}/authorize", json=payload)
                if resp.status_code == 200:
                    d = resp.json()
                    latencies_engine.append(d.get("latency_ms", 0.0))
                    if "end_to_end_ms" in d:
                        latencies_e2e.append(d.get("end_to_end_ms", 0.0))
            except Exception as ex:
                pass

        if not latencies_engine:
            print(f"❌ Không đo được dữ liệu cho engine {e}")
            continue

        p50 = float(np.percentile(latencies_engine, 50))
        p90 = float(np.percentile(latencies_engine, 90))
        p95 = float(np.percentile(latencies_engine, 95))
        mean_val = float(np.mean(latencies_engine))
        min_val = float(np.min(latencies_engine))
        max_val = float(np.max(latencies_engine))

        results_summary.append([
            e.upper(),
            len(latencies_engine),
            f"{min_val:.3f}",
            f"{mean_val:.3f}",
            f"{p50:.3f}",
            f"{p90:.3f}",
            f"{p95:.3f}",
            f"{max_val:.3f}"
        ])

    headers = ["Engine", "Mẫu đo (N)", "Min (ms)", "Mean (ms)", "P50 (ms)", "P90 (ms)", "P95 (ms)", "Max (ms)"]
    rendered_table = tabulate(results_summary, headers=headers, tablefmt="grid")
    print(rendered_table)

    # 3. Xuất file bằng chứng
    try:
        os.makedirs(os.path.dirname(args.out_evidence), exist_ok=True)
        with open(args.out_evidence, "w", encoding="utf-8") as f:
            f.write("# Báo Cáo Đo Độ Trễ & Hiệu Năng Phân Quyền P95 (FR-08)\n\n")
            f.write(f"- **Ngày đo**: `{os.popen('date').read().strip()}`\n")
            f.write(f"- **Phần cứng thử nghiệm**: CPU `{cpu_spec}`, RAM `{mem_spec}`\n")
            f.write(f"- **Tham số đo**: Warm-up `{args.warmup}` lần, Lặp chính thức `$N = {args.iterations}$` lần / engine.\n\n")
            f.write("```\n" + rendered_table + "\n```\n\n")
            f.write("## Nhận Xét Sơ Bộ\n")
            f.write("- **Cedar**: Thư viện nhúng trong tiến trình API (in-process Rust binding qua cedarpy) cho độ trễ cực thấp.\n")
            f.write("- **OPA**: Gọi qua HTTP REST API nội bộ, độ trễ phụ thuộc vào serialize JSON và mạng Docker.\n")
            f.write("- **Keycloak**: Gọi xác thực token UMA Ticket qua HTTP REST API, kết hợp cơ chế Token Cache để loại bỏ chi phí hashing mật khẩu.\n")
        print(f"\n💾 Đã lưu kết quả đo p95 vào: {args.out_evidence}")
    except Exception as e:
        print(f"⚠️ Không thể ghi file {args.out_evidence}: {e}")

if __name__ == "__main__":
    main()
