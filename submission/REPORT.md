# Báo cáo cá nhân — Day 13 Monitoring & LLMOps

## 1. Thông tin

- **Họ và tên:** Nguyễn Nhân Sâm
- **MSSV:** 2A202602672
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/Nguyen-Sam-sheep-zzz/K4-L3A-DAY13-NguyenNhanSam-2A202602672-Monitoring-LLMOps
- **Commit SHA cuối:** Lấy bằng `git rev-parse HEAD` sau khi commit/push và ghi vào LMS cùng URL repo. SHA không thể tự ghi vào nội dung của chính commit đó.
- **Langfuse project:** `day13-k4-l3a-2A202602672` theo ảnh chụp mới trong project cá nhân.
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1` từ release [Challenge File](https://github.com/VinUni-AI20k/K4-L3A-Day13-Monitoring-LLMOps/releases/tag/Challenge), asset `K4-L3A-challenge.json` cho K4-L3A. File gốc nằm tại `config/challenge.json` và đã được Git ignore.

## 2. Tóm tắt hệ thống

API FastAPI nhận `/chat`, tạo hoặc nhận `correlation_id`, chạy retrieval trên corpus mẫu, lấy prompt từ Langfuse theo label rồi gọi `FakeLLM`. `FakeLLM` chỉ mô phỏng model; token và cost là ước tính phục vụ lab. JSON logs được ghi vào `data/logs.jsonl`; Langfuse lưu trace và prompt versions. Giao diện thuyết trình ở `/demo` đọc logs 60 phút gần nhất và cập nhật mỗi 30 giây.

Luồng điều tra: **Metrics → Logs → Traces → Root cause**. Metrics chỉ triệu chứng và thời gian; log chỉ request bằng `correlation_id`; trace của request đó cho biết span `retrieval` hoặc `llm-generation` chậm/lỗi.

## 3. Kết quả kỹ thuật đã xác minh

| Nội dung | Baseline | Sau sửa | Giới hạn bằng chứng |
|---|---:|---:|---|
| Pytest | 5 failed, 22 passed (output người dùng cung cấp) | 29 passed | [01-pytest.txt](evidence/01-pytest.txt); chạy lại sau commit cuối nếu có thay đổi |
| Log validator | 30/100 trên 22 record cũ | 100/100 trên 114 record, 51 IDs, 0 PII leak | [02-log-validator.txt](evidence/02-log-validator.txt) |
| Dashboard validator | 6/6 | 6/6 | [03-dashboard-validator.txt](evidence/03-dashboard-validator.txt) chỉ kiểm tra YAML contract |
| Langfuse trace tree | Chưa có child spans | 20 trace hoàn chỉnh được đọc lại qua observations v2 API | Ảnh Cloud vẫn cần chụp |
| Prompt versions | Chưa có `day13-chat` | v1 `baseline`, v2 `candidate`; `production` promote v2 rồi rollback v1 | Readback qua Langfuse SDK; ảnh Cloud vẫn cần chụp |
| Demo dashboard 60 phút | Chưa có | 25 request, P95 4827 ms, retrieval success 100%, cost $0.049272, quality 0.824 tại lần đọc runtime | [11-dashboard-runtime.json](evidence/11-dashboard-runtime.json); giá trị thay đổi theo thời gian/workload |

## 4. Logging và PII

`app/middleware.py` xóa context cũ, chấp nhận `x-request-id` đúng mẫu `req-<8 hex>` hoặc sinh ID mới, bind vào structlog và trả lại trong response header cùng `x-response-time-ms`. `app/main.py` bind `user_id_hash`, `session_id`, `feature`, `model`, `env` trước event `request_received`. `app/logging_config.py` chạy scrubber đệ quy trước `JsonlFileProcessor` và `JSONRenderer`; `app/pii.py` che email, điện thoại Việt Nam, CCCD và thẻ thanh toán. User ID được băm trước khi ghi log/trace.

Log baseline cũ đã được giữ tại `.venv/logs-before-cp1.jsonl` (ignored) trước khi tạo log mới. Không dùng log cũ đó làm kết quả cuối.

## 5. Tracing và prompt versioning

Trace gồm root `lab-agent-run`, child `retrieval` và child `llm-generation` theo quan hệ cha-con. Retrieval ghi số tài liệu và trạng thái; generation ghi model `fake-llm`, managed prompt, input/output tokens và cost. Metadata có `correlation_id`, prompt name/label/version; chỉ preview đã scrub được gửi, không capture raw prompt/output.

Trong project Langfuse cá nhân, prompt `day13-chat` có ba biến `{{feature}}`, `{{docs}}`, `{{message}}`. V1 gắn `baseline`, v2 gắn `candidate`. Cùng một input được chạy hai lần:

| Label | Version | Correlation ID | Trace ID |
|---|---:|---|---|
| baseline | 1 | `req-4e51cc58` | `261c77b99b7aca51597b19caa66fd4b7` |
| candidate | 2 | `req-abd0a755` | `47947d632e5101e286fa49baeaf94d53` |

`production` đã được chuyển sang v2 và đọc lại thành v2, rồi rollback về v1 và đọc lại thành v1. Các request chạy sau đó có `prompt_source=langfuse` và `prompt_version=1`; một số request đầu vẫn có `local-fallback` khi prompt fetch chưa thành công, nên không tính chúng là bằng chứng managed prompt.

## 6. Dashboard, SLO và alerts

`/demo` hiển thị đúng sáu nhóm dữ liệu theo `config/dashboard.yaml`: latency/TTFT, traffic, errors/retrieval success, cost, tokens và quality proxy. Dữ liệu lấy từ `data/logs.jsonl` trong 60 phút gần nhất; `config/dashboard.yaml` là contract cho tên, đơn vị, phép tổng hợp và threshold. `quality_score` là heuristic proxy, không phải đánh giá chất lượng câu trả lời bởi người dùng.

`config/slo.yaml` đặt SLO **99.5% request thành công trong 3000 ms** trên cửa sổ 28 ngày. Error budget là **0.5%** tổng request, tức khoảng **50/10.000 request** được phép không đạt SLO. Ngưỡng này là mục tiêu lab; khi dùng production cần hiệu chỉnh bằng baseline dài hơn. Ba alert trong `config/alert_rules.yaml` theo triệu chứng: P95 latency > 3000 ms trong 5 phút, error rate > 2% trong 5 phút, retrieval success < 90% trong 10 phút. `docs/alerts.md` có bước điều tra và mitigation. Repo chưa có alert engine/Slack webhook thật; rule và channel là định nghĩa để tích hợp.

## 7. Incident practice và challenge chính thức

Practice `rag_slow` được bật rồi tắt. Request `req-7e501e84` có latency **4827 ms**, vượt threshold 3000 ms. Log cùng ID và Langfuse trace `2844258f57931b1cc379355076f1226e` cho thấy child `retrieval` mất **2.502 s**, `llm-generation` mất **0.151 s**. Nguyên nhân được tiêm vào practice là retrieval bị làm chậm; trace chứng minh retrieval đóng góp ít nhất 2.502 s vào request này. Phần thời gian còn lại chưa được tách thành span riêng nên không quy toàn bộ 4.827 s cho retrieval. Fix action: tắt scenario, sau đó kiểm tra latency giảm. Preventive measure: alert P95 và đo riêng retrieval span.

**Challenge chính thức:** Release công khai của repository K4-L3A có asset `K4-L3A-challenge.json`, SHA-256 `B11E6286F35CDE0D744ADC5EDCB5E0A9CDFFCA865EB281B2C481219B2C86F6BF`. File khai báo incident `rag_slow`, feature `monitoring`, ngưỡng **2000 ms** và 5 query. File này được tải nguyên bản vào `config/challenge.json`, không commit hoặc chép nội dung query/seed vào evidence.

Chạy cùng 5 query ở chế độ bình thường cho **5/5 HTTP 200**, log server ghi latency **151–152 ms**. Sau khi bật incident và chạy `python scripts/load_test.py --challenge --concurrency 5`, **5/5 vẫn HTTP 200** nhưng log server ghi **2651–2652 ms**, tất cả vượt 2000 ms. Khoảng response UTC là **2026-09-29 10:00:12.845848–10:00:23.468266**. Đây là suy giảm latency, không phải lỗi HTTP; dashboard tổng hợp 60 phút sau run có P95 **2652 ms** và error rate **0%**. Client load test in thời gian 7973–13288 ms; giá trị này gồm xếp hàng/chờ ở phía client và không đồng nhất với `latency_ms` đo bên trong agent. API đang gọi phần đồng bộ trong endpoint async, nên workload đồng thời có thể chờ nối tiếp; không quy toàn bộ thời gian client cho retrieval.

Chuỗi điều tra một request: **metric** 2651 ms > 2000 ms → **log** `response_sent`, `correlation_id=req-b608e906`, timestamp `2026-09-29T10:00:12.845848Z` → **trace** `0ca3b57f44aae866066af3af1b1bf959` cùng correlation ID → child `retrieval` **2.501 s**, child `llm-generation` **0.151 s**. Trace này còn ghi managed prompt `day13-chat/production/v1`, model `fake-llm`, 34 input + 127 output tokens, estimated cost `$0.002007`. Incident cấu hình làm chậm retrieval; span cho thấy đây là thành phần gây tăng thời gian xử lý. So với 151–152 ms baseline, mức tăng latency server xấp xỉ 2,5 giây. Fix action: tắt `rag_slow`, xác nhận `/health` báo `false`; trong hệ thống thật cần kiểm tra backend truy xuất tài liệu, timeout và cache. Preventive measure: theo dõi P95 và riêng retrieval span, đặt alert theo ngưỡng, áp dụng timeout/fallback và chạy thử tải đồng thời để phát hiện chờ nối tiếp. Threshold **2000 ms** là của challenge; panel dashboard demo vẫn hiển thị SLO chung **3000 ms** theo `config/dashboard.yaml`.

Evidence CP3: [metric](evidence/12-incident-metric.txt), [log](evidence/13-incident-log.txt), [trace](evidence/14-incident-trace.txt), kèm ảnh [dashboard](evidence/11-dashboard-cp3.png), [log](evidence/13-incident-log.png) và [trace](evidence/14-incident-trace.png). Ảnh trace có đúng trace ID và cây hai bước; `correlation_id` chưa hiện trong cùng ảnh vì ảnh đang chọn generation. Readback SDK và log nối cùng ID trong các file text.

## 8. Quyết định kỹ thuật, blocker và điều học được

- **Quyết định:** Giữ log JSONL là nguồn chuẩn của dashboard, còn Langfuse là nguồn trace/prompt. Điều này giúp demo hoạt động khi Langfuse tạm thời không truy cập được, đồng thời `correlation_id` vẫn nối được hai nguồn.
- **Blocker:** Prompt `day13-chat` ban đầu chưa tồn tại nên trace ghi `local-fallback`. Đã tạo prompt v1/v2, xác minh readback rồi chạy lại workload; hai trace so sánh hiện ghi `prompt_source=langfuse`.
- **Bài học:** Một API trả HTTP 200 chưa đủ chứng minh hệ thống vận hành tốt. Cần quan sát tail latency, lỗi, cost, dữ liệu nhạy cảm và khả năng truy ngược request đến từng span.
- **Giới hạn:** Ảnh metadata chứa `correlation_id` trong Langfuse và ảnh lúc `production` ở v2 còn thiếu; ảnh trạng thái rollback về v1 đã có. SHA cuối phải lấy từ remote khi nộp. Thông báo Slack chưa được triển khai. `FakeLLM` không chứng minh hành vi hoặc chi phí của model thật.

## 9. Evidence index

Các file text dưới đây chứa readback hoặc dữ liệu runtime thật. Ảnh dashboard mới cho thấy P95 2652 ms sau CP3; panel hiển thị SLO chung 3000 ms, còn ngưỡng challenge 2000 ms nằm trong evidence metric. Dashboard hiển thị threshold dưới dạng chữ, chưa có đường SLO trực quan. Ảnh trace metadata hiện chỉ cho thấy một phần các trường; file text readback có metadata đầy đủ.

| Evidence hiện có | Đường dẫn |
|---|---|
| Pytest cuối | [01-pytest.txt](evidence/01-pytest.txt) |
| Log validator | [02-log-validator.txt](evidence/02-log-validator.txt) |
| Dashboard validator | [03-dashboard-validator.txt](evidence/03-dashboard-validator.txt) |
| Structured log an toàn | [04-structured-log.json](evidence/04-structured-log.json) |
| PII redaction runtime | [05-pii-redaction.json](evidence/05-pii-redaction.json) |
| Danh sách traces thật | [06-trace-list.txt](evidence/06-trace-list.txt) |
| Ảnh trace list của project cá nhân | [06-trace-list.png](evidence/06-trace-list.png) |
| Ảnh trace list mới, tên project đủ MSSV | [06-trace-list-current.png](evidence/06-trace-list-current.png) |
| Quan hệ cha-con của một trace | [07-trace-waterfall.txt](evidence/07-trace-waterfall.txt) |
| Ảnh trace tree | [07-trace-waterfall.png](evidence/07-trace-waterfall.png) |
| Prompt/model/token/cost metadata | [08-trace-metadata.txt](evidence/08-trace-metadata.txt) |
| Ảnh generation detail một phần | [08-generation-detail.png](evidence/08-generation-detail.png) |
| Hai trace với baseline/candidate | [08-prompt-trace-comparison.txt](evidence/08-prompt-trace-comparison.txt) |
| Prompt versions | [09-prompt-versions.txt](evidence/09-prompt-versions.txt) |
| Ảnh prompt versions | [09-prompt-versions-a.png](evidence/09-prompt-versions-a.png), [09-prompt-versions-b.png](evidence/09-prompt-versions-b.png) |
| Promote/rollback readback | [10-prompt-rollback.txt](evidence/10-prompt-rollback.txt) |
| Ảnh sau rollback: production ở v1 | [10-prompt-rollback-after.png](evidence/10-prompt-rollback-after.png) |
| Dashboard runtime snapshot | [11-dashboard-runtime.json](evidence/11-dashboard-runtime.json) |
| Ảnh 6 panel dashboard trước CP3 | [11-dashboard-overview.png](evidence/11-dashboard-overview.png) |
| Ảnh 6 panel dashboard sau CP3 | [11-dashboard-cp3.png](evidence/11-dashboard-cp3.png) |
| Challenge metric | [12-incident-metric.txt](evidence/12-incident-metric.txt) |
| Dashboard sau CP3 (snapshot cửa sổ 60 phút) | [12-incident-dashboard.json](evidence/12-incident-dashboard.json) |
| Challenge log | [13-incident-log.txt](evidence/13-incident-log.txt) |
| Ảnh challenge log | [13-incident-log.png](evidence/13-incident-log.png) |
| Challenge trace | [14-incident-trace.txt](evidence/14-incident-trace.txt) |
| Ảnh challenge trace tree | [14-incident-trace.png](evidence/14-incident-trace.png) |
| Practice metric | [12-practice-incident-metric.txt](evidence/12-practice-incident-metric.txt) |
| Practice log | [13-practice-incident-log.txt](evidence/13-practice-incident-log.txt) |
| Practice trace | [14-practice-incident-trace.txt](evidence/14-practice-incident-trace.txt) |

## 10. Checklist trước khi nộp

- [ ] Cập nhật repository URL và commit SHA cuối.
- [ ] Lưu output pytest và validators trên commit cuối.
- [x] Có ảnh Langfuse project cá nhân: ≥10 traces, waterfall, v1/v2; không mở trang API Keys.
- [ ] Chụp thêm root metadata chứa correlation ID và ảnh lúc production ở v2; ảnh sau rollback về v1 đã có.
- [x] Có ảnh dashboard runtime `/demo` với sáu panel, dữ liệu, 60 phút, đơn vị và threshold dạng chữ.
- [x] Có ảnh dashboard, log và trace tree đúng phiên CP3; correlation ID trong ảnh Langfuse cần chụp bổ sung để nối trực quan với log.
- [x] Đã chạy challenge chính thức từ release K4-L3A và tắt incident sau thử nghiệm.
- [ ] Rà Git để bảo đảm `.env`, secrets, raw PII, `.venv` và `config/challenge.json` không được commit.
