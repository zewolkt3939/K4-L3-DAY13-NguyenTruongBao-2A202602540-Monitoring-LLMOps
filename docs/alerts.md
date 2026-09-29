# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

<a id="alert-1"></a>
## Alert 1: high_latency_p95

- **Tên:** high_latency_p95
- **Severity:** warning
- **Duration:** 5m
- **Kênh thông báo:** Slack (#alerts-llmops)
- **SLI/SLO liên quan:** `primary_slo` (Latency P95 <= 3000ms trong 28 ngày)
- **Điều kiện và thời gian duy trì:** Latency P95 > 3000ms duy trì liên tục trong 5 phút.
- **Ảnh hưởng tới người dùng:** Người dùng trải nghiệm phản hồi chậm, thời gian chờ sinh câu trả lời kéo dài, có nguy cơ timeout client.
- **Ba bước kiểm tra đầu tiên:**
  1. Mở Panel Latency trên Dashboard để xác định thời điểm bắt đầu tăng vọt và giá trị TTFT (Time To First Token).
  2. Lọc `data/logs.jsonl` tìm các event `response_sent` có `latency_ms > 3000` trong 15 phút qua, lấy danh sách `correlation_id`.
  3. Mở Langfuse trace theo `correlation_id` để kiểm tra Waterfall view: so sánh thời gian thực thi của span `retrieval` và span `generation`.
- **Mitigation tạm thời:**
  - Nếu span `retrieval` bị nghẽn: giảm số lượng document retrieve hoặc bật cache/chuyển sang fallback search.
  - Nếu span `generation` chậm: kiểm tra số lượng output tokens hoặc chuyển sang mô hình phản hồi nhanh hơn nếu cần.
- **Owner:** llmops-oncall

<a id="alert-2"></a>
## Alert 2: high_error_rate

- **Tên:** high_error_rate
- **Severity:** critical
- **Duration:** 3m
- **Kênh thông báo:** Slack (#alerts-critical-sev1)
- **SLI/SLO liên quan:** `guardrails.error_rate_pct_max` (Error rate <= 2%)
- **Điều kiện và thời gian duy trì:** Tỷ lệ lỗi `count(request_failed) / count(request_received) * 100 > 2%` duy trì trong 3 phút.
- **Ảnh hưởng tới người dùng:** Người dùng nhận phản hồi lỗi HTTP 500 / request_failed, không nhận được câu trả lời từ trợ lý AI.
- **Ba bước kiểm tra đầu tiên:**
  1. Mở Panel Errors trên Dashboard để xem `error_rate_pct` và breakdown `error_type` (e.g., RuntimeError, TimeoutError).
  2. Truy vấn `data/logs.jsonl` với `event == "request_failed"` để lấy log chi tiết và `payload.detail`.
  3. Mở Langfuse trace tương ứng bằng `correlation_id`, kiểm tra span nào bị gán cờ `status_message: ERROR` (ví dụ retrieval vector store timeout).
- **Mitigation tạm thời:**
  - Nếu do retrieval component bị lỗi (`tool_fail`): kích hoạt cơ chế fallback trả lời không qua retrieval hoặc restart vector database pod/service.
  - Thông báo incident cho team liên quan và bật trang thông báo bảo trì/giảm tải nếu cần.
- **Owner:** llmops-oncall

<a id="alert-3"></a>
## Alert 3: daily_cost_budget_breach

- **Tên:** daily_cost_budget_breach
- **Severity:** warning
- **Duration:** 10m
- **Kênh thông báo:** Slack (#alerts-finops)
- **SLI/SLO liên quan:** `guardrails.daily_cost_usd_max` (Chi phí tối đa 2.5 USD / ngày)
- **Điều kiện và thời gian duy trì:** Tổng chi phí tích lũy trong ngày `sum(cost_usd) > 2.5 USD` duy trì trạng thái vượt ngân sách.
- **Ảnh hưởng tới người dùng:** Chưa ảnh hưởng trực tiếp đến người dùng, nhưng đe dọa ngân sách vận hành của doanh nghiệp và có thể dẫn đến việc cắt giảm tài nguyên sau đó.
- **Ba bước kiểm tra đầu tiên:**
  1. Mở Panel Cost và Tokens trên Dashboard để xem tốc độ tiêu thụ token (`tokens_in`, `tokens_out`).
  2. Xác định xem chi phí tăng do đột biến lưu lượng (traffic spike) hay do prompt/completion output tokens tăng bất thường (`cost_spike`).
  3. Kiểm tra Langfuse prompt versions và generation metadata xem có prompt version nào sinh output quá dài hoặc lặp vô tận không.
- **Mitigation tạm thời:**
  - Giới hạn `max_tokens` cho câu trả lời generation hoặc áp dụng rate limit đối với các user/session tiêu thụ bất thường.
  - Rollback prompt về version trước đó nếu phát hiện prompt candidate mới gây bùng nổ token.
- **Owner:** llmops-finops
