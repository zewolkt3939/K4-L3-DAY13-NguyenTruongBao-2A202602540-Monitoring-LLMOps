# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Trường Bảo
- **MSSV:** 2A202602540
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/zewolkt3939/K4-L3-DAY13-NguyenTruongBao-2A202602540-Monitoring-LLMOps.git
- **Commit SHA cuối:** 7ff0aac
- **Challenge ID:** (Sẽ cập nhật khi nhận file config/challenge.json từ Lab Coach)
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602540`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Hoàn thành toàn bộ schema, correlation ID propagation, context enrichment và PII scrubbing |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Hợp lệ toàn bộ 6 panel contract theo chuẩn specs |
| `pytest` | 22 passed | 24 passed | 100% testsuite pass (đã bổ sung test CCCD và thẻ) |
| Số traces hợp lệ | 0 | >= 10 traces | Đầy đủ quan hệ cha-con (root -> retrieval, generation) trên project cá nhân |
| Số PII leak | 0 | 0 | 0 rò rỉ PII nguyên văn trong log và trace metadata |
| Latency P95 / TTFT P95 | 157ms / 50ms | 151ms / 50ms | Nằm trong ngưỡng an toàn của SLO (<= 3000ms) |
| Retrieval success rate | 100% | 100% | Hoạt động chính xác, ổn định ở baseline |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Trong `app/middleware.py`, middleware gọi `clear_contextvars()` trước mỗi request để tránh rò rỉ dữ liệu giữa các request đồng thời. Middleware trích xuất header `x-request-id` từ client, nếu rỗng thì tự động sinh ID dạng `req-<8-hex>` (`f"req-{uuid.uuid4().hex[:8]}"`). Sau đó bind vào structlog contextvars và gán vào `request.state.correlation_id`. Cuối cùng trả lại ID trong response header `x-request-id` và thời gian phản hồi trong `x-response-time-ms`.
- **Các metadata được ghi vào structured log:** Các trường toàn cục gồm `ts` (ISO UTC), `level`, `service`, `event`, `correlation_id`. Khi xử lý API `/chat`, bổ sung các trường context enrichment: `user_id_hash` (băm sha256 12 ký tự), `session_id`, `feature`, `model` (`claude-sonnet-4-5`), `env` (`dev`). Log `response_sent` bổ sung `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`, và `payload`.
- **Cách bảo đảm PII được scrub trước khi ghi:** Xây dựng hàm `_scrub_value` đệ quy trong `app/logging_config.py` và đăng ký processor `scrub_event` vào chuỗi processor của structlog **ngay trước** `JsonlFileProcessor` và `JSONRenderer`. Nhờ đó, mọi trường trong payload (email, SĐT VN, CCCD, thẻ thanh toán, passport) đều được thay thế bằng token `[REDACTED_*]` trước khi chuỗi JSON được serialize và ghi xuống đĩa hoặc stdout.
- **Cách kiểm chứng kết quả:** Tự động kiểm chứng bằng `scripts/validate_logs.py` (đạt 100/100 điểm, 0 PII leak) và chạy `pytest tests/test_pii.py` kiểm tra toàn bộ regex.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Traces hiển thị trên project Langfuse Cloud riêng mang tên `day13-k4-l3a-2A202602540`. Mỗi trace mang `user_id` dạng hash, session ID, tag `["lab", feature, model]` và metadata chứa `correlation_id` khớp chính xác với log ứng dụng.
- **Cấu trúc root/retrieval/generation observations:** Root observation là `lab-agent-run` (type `agent`). Dưới root gồm 2 child observations: `retrieval` (type `retriever` đo thời gian tra cứu tài liệu) và `generation` (type `generation` đo thời gian gọi FakeLLM, ghi nhận `model`, `usage_details` và `cost_details`).
- **Cách nối trace với log:** Thông qua `correlation_id`: middleware sinh hoặc nhận ID và lưu vào `request.state.correlation_id`, sau đó agent gán `correlation_id` này vào metadata của trace Langfuse và structured log `data/logs.jsonl`.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1 gắn label `baseline`
- **Version/label candidate:** Version 2 gắn label `candidate`
- **Trace ID của mỗi version:** Ghi nhận từ giao diện Langfuse sau khi gửi workload tương ứng với từng label.
- **Cách promote và rollback `production`:** Tại giao diện Langfuse Prompts, chọn Version 2 và gán label `production` để promote. Để rollback, chọn lại Version 1 và gán lại label `production`.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** 
  1. Panel Latency: P50, P95, P99 và TTFT (ms), threshold P95 <= 3000ms.
  2. Panel Traffic: Số request nhận được và rate/min, threshold >= 1 req/min.
  3. Panel Errors: Tỷ lệ lỗi %, breakdown lỗi và retrieval success rate, threshold <= 2%.
  4. Panel Cost: Tổng chi phí tích lũy theo cửa sổ và theo phút, threshold <= $2.50.
  5. Panel Tokens: Input tokens và output tokens, threshold <= 50,000.
  6. Panel Quality: Điểm chất lượng trung bình (0.0 - 1.0), threshold >= 0.75.
- **SLO và lý do chọn:** Primary SLO quy định trong 28 ngày, 99.5% request gửi đến hệ thống phải phản hồi thành công với latency <= 3000ms. Ngưỡng 3000ms đảm bảo người dùng không phải chờ đợi lâu khi tương tác với chatbot AI và ngăn chặn tình trạng client timeout.
- **Cách tính error budget:** Error budget = $100\% - 99.5\% = 0.5\%$. Nếu hệ thống phục vụ 10,000 request trong chu kỳ 28 ngày, error budget cho phép tối đa 50 request bị chậm (>3000ms) hoặc trả về lỗi.
- **Ba alert và runbook tương ứng:**
  1. `high_latency_p95`: Cảnh báo khi Latency P95 > 3000ms trong 5 phút. Runbook tại `docs/alerts.md#alert-1`.
  2. `high_error_rate`: Cảnh báo khi Error rate > 2% trong 3 phút. Runbook tại `docs/alerts.md#alert-2`.
  3. `daily_cost_budget_breach`: Cảnh báo khi chi phí tích lũy > 2.5 USD trong 10 phút. Runbook tại `docs/alerts.md#alert-3`.

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
