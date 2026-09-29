# Alerts và runbook

Các rule trong `config/alert_rules.yaml` là định nghĩa vận hành cho lab. Repo chưa có Slack webhook hoặc alert engine chạy thật; kênh `#day13-llmops-alerts` là nơi dự kiến gửi thông báo khi tích hợp hệ thống cảnh báo.

## Alert 1

- **Tên:** `high_latency_p95`; severity `warning`; owner `on-call-student`.
- **Điều kiện:** P95 latency của `response_sent` > 3000 ms liên tục 5 phút.
- **Ảnh hưởng:** Người dùng chờ câu trả lời lâu; đe dọa SLO 99.5% request thành công trong 3 giây.
- **Kiểm tra:** (1) Xem panel latency/TTFT và khoảng thời gian; (2) lọc log `response_sent` chậm, lấy `correlation_id`; (3) mở trace cùng ID, so thời gian `retrieval` và `llm-generation`.
- **Mitigation:** Nếu retrieval chậm, kiểm tra dịch vụ tìm kiếm, giới hạn concurrency và dùng fallback có kiểm soát. Nếu generation chậm, giảm tải hoặc đổi model theo chính sách.
- **Kênh:** Slack `#day13-llmops-alerts` khi có alert engine.

## Alert 2

- **Tên:** `high_error_rate`; severity `critical`; owner `on-call-student`.
- **Điều kiện:** `request_failed / request_received` > 2% liên tục 5 phút.
- **Ảnh hưởng:** Request lỗi HTTP 500, người dùng không nhận được câu trả lời.
- **Kiểm tra:** (1) Xem panel errors và `error_type`; (2) tìm log `request_failed` và `correlation_id`; (3) mở trace để xác định span lỗi và xác nhận dependency.
- **Mitigation:** Dừng thay đổi vừa triển khai nếu trùng thời điểm, kiểm tra retrieval dependency, dùng fallback an toàn và theo dõi error rate phục hồi.
- **Kênh:** Slack `#day13-llmops-alerts` khi có alert engine.

## Alert 3

- **Tên:** `low_retrieval_success`; severity `warning`; owner `on-call-student`.
- **Điều kiện:** `tool_success == true / tool_success != null` < 90% liên tục 10 phút.
- **Ảnh hưởng:** Thiếu tài liệu để trả lời; chất lượng hoặc tỷ lệ thành công giảm.
- **Kiểm tra:** (1) Xem panel errors/retrieval; (2) lọc log `tool_success=false`; (3) mở trace cùng `correlation_id` để xem span retrieval.
- **Mitigation:** Kiểm tra vector store, retry có giới hạn và dùng câu trả lời fallback minh bạch khi không có tài liệu.
- **Kênh:** Slack `#day13-llmops-alerts` khi có alert engine.
