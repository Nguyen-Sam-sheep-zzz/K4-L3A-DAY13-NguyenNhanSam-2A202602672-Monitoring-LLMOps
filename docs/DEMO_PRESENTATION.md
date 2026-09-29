# Kịch bản thuyết trình Day 13

## Chuẩn bị

1. Mở hai terminal trong repo và activate `.venv` ở cả hai.
2. Terminal 1: `python -m uvicorn app.main:app --reload --env-file .env`. Giữ terminal này chạy.
3. Terminal 2: `python scripts/load_test.py` để có 10 request; mở `http://127.0.0.1:8000/demo`.
4. Mở project Langfuse cá nhân ở tab khác; đặt time range gần nhất. Không mở/chụp trang API Keys.
5. Dùng dữ liệu test của repo; tắt mọi incident practice sau demo.

## Lời trình bày 3–5 phút

**Mở đầu:** “Bài này biến một API AI mẫu thành hệ thống có thể quan sát. FakeLLM mô phỏng câu trả lời nên không tốn phí model thật. Tôi theo dõi request bằng ba lớp: metrics, logs và traces.”

**Chat demo:** Gửi câu “Explain monitoring...” ở tab Chat. Chỉ HTTP 200, `correlation_id`, latency, TTFT, token và cost. Giải thích token/cost là ước tính trong mô phỏng. `correlation_id` là khóa nối giữa response, log và Langfuse trace.

**Dashboard:** Mở tab Observability. Sáu panel gồm latency P50/P95/P99 và TTFT P95; traffic; error/retrieval success; cost; tokens; quality proxy. Panel lấy dữ liệu từ `data/logs.jsonl` trong 60 phút gần nhất, không lấy từ ảnh tĩnh. P95 có ích vì phản ánh nhóm request chậm hơn average.

**Trace:** Mở Langfuse, tìm trace có `correlation_id` cùng log. Chỉ root `lab-agent-run`, child `retrieval` và `llm-generation`. Trên generation chỉ model, prompt version/label, token/cost và preview đã che PII. Nếu thấy `prompt_source=local-fallback`, phải nói rõ chưa lấy được managed prompt; không gọi đó là evidence prompt version.

**Incident practice:** Bật “RAG chậm”, gửi lại câu hỏi; latency P95 tăng. Lấy request chậm từ log và mở trace cùng ID; nếu span `retrieval` dài, kết luận nghẽn retrieval trong practice. Tắt incident sau demo. Với challenge chính thức, chỉ dùng file đúng lớp do Lab Coach cấp và ghi metric/log/trace cùng một sự cố.

**Kết:** “SLO đặt 99.5% request thành công trong 3 giây trên cửa sổ 28 ngày, nên error budget là 0.5%. Ba alert theo triệu chứng gồm latency cao, error rate cao và retrieval success thấp. Prompt có v1/v2 và label production; rollback giúp trở về version ổn định khi có sự cố.”

## Câu hỏi thường gặp

| Câu hỏi | Trả lời ngắn |
|---|---|
| Vì sao cần cả metrics, logs, traces? | Metrics chỉ triệu chứng; logs chỉ request; traces chỉ bước gây vấn đề. |
| Correlation ID khác trace ID thế nào? | Correlation ID là mã ứng dụng cho một request và được gắn vào log/trace; trace ID là mã của cây observation trong Langfuse. |
| PII được bảo vệ ở đâu? | Scrubber chạy trước JSON render/ghi file; trace chỉ ghi preview đã scrub và ID băm. |
| Vì sao dùng fake model? | Lab đánh giá khả năng quan sát và vận hành, không đánh giá chất lượng model trả phí. |
| Validator 6/6 chứng minh điều gì? | Cấu trúc dashboard YAML hợp lệ; vẫn cần dashboard runtime có dữ liệu. |
| Error budget 0.5% nghĩa là gì? | Trong 10.000 request, tối đa khoảng 50 request không đạt SLO trước khi vượt ngân sách. |

## Lệnh kiểm chứng cuối

```powershell
python -m pytest -q
python scripts/validate_logs.py
python scripts/validate_dashboard.py
```

Đưa output thật và ảnh thật vào `submission/evidence/`. Không dựng bằng chứng thay cho Langfuse Cloud hoặc challenge chính thức.
