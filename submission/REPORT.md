# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Trường Bảo
- **MSSV:** 2A202602540
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/zewolkt3939/K4-L3-DAY13-NguyenTruongBao-2A202602540-Monitoring-LLMOps.git
- **Commit SHA cuối:** 92777ff
- **Challenge ID:** day13-k4-l3a-monitoring-llmops-v1
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
| `pytest` | 22 passed | 25 passed | 100% testsuite pass (đã bổ sung test CCCD, thẻ và audit system) |
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

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 2026-09-29 09:51:00 UTC - 09:51:30 UTC
- **Triệu chứng từ metrics:** Latency P95 tăng vọt từ baseline 151ms lên 2,652ms (+1,656%), độ trễ ghi nhận phía client đo được từ 5,320ms đến 13,290ms khi chạy ở mức concurrency = 5. Toàn bộ 5/5 query của challenge đều vượt ngưỡng `latency_threshold_ms: 2000` và vi phạm SLO. Tỷ lệ lỗi (error rate) vẫn ở mức 0.0%, chất lượng phản hồi không đổi, nhưng hệ thống bị suy giảm hiệu năng nghiêm trọng do độ trễ quá cao.
- **Log line và correlation ID liên quan:**
  - Request điển hình: `correlation_id: req-c80160d2` (cùng các request trong đợt tải: `req-bc8a70df`, `req-f4582529`, `req-35982250`, `req-f7f5afa4`).
  - Log `response_sent`:
    ```json
    {"service": "api", "latency_ms": 2652, "ttft_ms": 50, "tokens_in": 32, "tokens_out": 128, "cost_usd": 0.002016, "quality_score": 0.8, "tool_name": "retrieval", "tool_success": true, "event": "response_sent", "env": "dev", "user_id_hash": "138341daeeaa", "correlation_id": "req-c80160d2", "feature": "monitoring", "session_id": "k4-l3a-challenge-s01", "model": "claude-sonnet-4-5", "level": "info", "ts": "2026-09-29T09:51:18.201844Z"}
    ```
- **Trace ID và span gây ảnh hưởng:**
  - Trace ID / Correlation ID: `req-c80160d2`
  - Root observation: `lab-agent-run` (thời gian thực thi tổng: 2,652ms)
  - Span con `retrieval` (loại `retriever`): Thời gian thực thi là **2,502ms**, chiếm tới **94.3%** tổng thời gian request.
  - Span con `generation` (loại `generation`): Thời gian thực thi chỉ **150ms** (5.7%), TTFT là **50ms**.
- **Root cause:** Bước truy xuất tài liệu vector store (`retrieve()` trong `app/mock_rag.py`) bị suy thoái hiệu năng nghiêm trọng do sự cố `rag_slow` (mô phỏng vector store bị quá tải hoặc nghẽn kết nối mạng), gây ra độ trễ nhân tạo 2.5 giây. Khâu gọi LLM sinh văn bản hoàn toàn bình thường.
- **Fix action:**
  1. Tắt sự cố mô phỏng bằng lệnh `python scripts/inject_incident.py --disable`.
  2. Bổ sung cơ chế caching cho các câu truy vấn retrieval phổ biến và thiết lập connection pooling cho vector database.
- **Preventive measure:**
  1. Thiết lập giới hạn hard timeout cho bước retrieval là 500ms: nếu vector search quá 500ms thì fallback sang keyword search hoặc trả lời bằng kiến thức nền mà không làm gián đoạn/treo toàn bộ request của người dùng.
  2. Triển khai Circuit Breaker cho module retrieval và cấu hình alert `high_latency_p95` (P95 > 3000ms duy trì 5 phút) để cảnh báo sớm cho đội ngũ On-call.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Đăng ký processor `scrub_event` vào chuỗi processor của structlog ngay **trước** `JsonlFileProcessor` và `JSONRenderer`. Quyết định này đảm bảo dữ liệu PII được làm sạch ở mức gốc (source of truth) trước khi ghi xuống file log đĩa hoặc stdout, tránh tình trạng "lộ PII rồi mới che" hoặc che thiếu sót.
- **Một lỗi/blocker đã gặp:** Gặp lỗi `[WinError 10048]` (cổng 8000 bị chiếm dụng bởi tiến trình chạy nền cũ) và `PermissionError` với thư mục tạm mặc định của pytest trên hệ điều hành Windows.
- **Cách tìm nguyên nhân và xử lý:** Dùng PowerShell `Get-NetTCPConnection` để tìm PID chiếm cổng 8000 và dừng tiến trình bằng `Stop-Process`; cấu hình `pytest.ini` với `--basetemp=.pytest_tmp` và thêm vào `.gitignore` để kiểm thử pytest hoạt động ổn định trên môi trường Windows.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  - Metrics là "hồi chuông cảnh báo" (triệu chứng + thời gian): cho biết P95 latency tăng vọt lúc nào.
  - Logs là "danh sách nạn nhân" (request cụ thể): dùng bộ lọc thời gian và feature để tìm ra các request bị chậm và trích xuất `correlation_id`.
  - Traces là "khám nghiệm chi tiết" (nguyên nhân gốc rễ): dùng `correlation_id` mở Waterfall view trên Langfuse để biết chính xác span `retrieval` là nguyên nhân, loại trừ span `generation`.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  - Prompt versioning & Rollback: Đảm bảo có thể kiểm soát và quay xe tức thì khi prompt mới gây ảo giác, tăng latency hoặc bùng nổ token/chi phí.
  - Token & Cost monitoring: Ngăn chặn hiện tượng cạn kiệt ngân sách do prompt lặp hoặc input/output quá dài.
  - SLO: Đặt ra ranh giới dịch vụ rõ ràng giữa trải nghiệm khách hàng và chi phí vận hành.
- **Điều quan trọng nhất đã học:** Nắm vững quy trình Observability chuẩn chỉ trong LLMOps: không điều tra theo cảm tính mà luôn đi theo chuỗi bằng chứng xác thực Metrics $\rightarrow$ Logs $\rightarrow$ Traces.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Các metric hiện đang lưu trữ in-memory và tính toán từ file log JSONL local; trong môi trường production quy mô lớn, nên đẩy metric lên Prometheus/Grafana và log lên Elasticsearch/Loki.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.

## 10. Điểm thưởng (Bonus — Tối đa +10 điểm)

Theo quy định tại `docs/RUBRIC.md` Section H, bài làm đã triển khai hoàn thiện 2 giải pháp kỹ thuật nâng cao đạt mức điểm thưởng tối đa (+10 điểm):

### 1. Automation & Pre-flight Security Scanner (+5 điểm)
- **Mục đích:** Tự động hóa quá trình rà soát an ninh và tính toàn vẹn của mã nguồn trước khi nộp bài hoặc triển khai CI/CD.
- **Tập lệnh triển khai:** `scripts/security_scan.py`
- **Các tầng kiểm tra tự động (4 tầng):**
  1. *Secrets & Credentials Scan:* Quét toàn bộ file được track bởi Git bằng regex để phát hiện các secret bị rò rỉ (Langfuse Secret Keys `sk-lf-*`, OpenAI Keys `sk-*`, AWS Access Keys `AKIA*`, RSA/SSH Private Keys).
  2. *Sensitive Files Exclusion:* Xác thực `.env` và `config/challenge.json` được chặn hoàn toàn bởi `.gitignore`, không bao giờ bị lộ ra remote repo.
  3. *Log PII Scrubbing Validation:* Quét sâu từng dòng trong file log runtime `data/logs.jsonl` để phát hiện và cảnh báo nếu có PII thô (email, SĐT Việt Nam, CCCD 12 số, thẻ thanh toán 16 số).
  4. *Evidence Links Integrity:* Kiểm tra tự động 15 đường dẫn tương đối trong `submission/REPORT.md`, đảm bảo tất cả file evidence trong `submission/evidence/` đều tồn tại và hợp lệ.
- **Lệnh thực thi:**
  ```powershell
  python scripts/security_scan.py
  ```

### 2. Compliance Audit Logging System (+5 điểm)
- **Mục đích:** Cung cấp hệ thống ghi log kiểm toán độc lập (Compliance Audit Log) dành riêng cho các sự kiện quản trị, thay đổi cấu hình, can thiệp sự cố (incident injection/recovery) với chu kỳ lưu trữ (retention) và định dạng chuẩn hóa.
- **Các thành phần triển khai:**
  - *Schema chuẩn:* `config/audit_schema.json` quy định chặt chẽ cấu trúc JSON Schema (draft 2020-12) với các trường bắt buộc: `ts`, `actor`, `action`, `resource`, `status`, `retention_days` (mặc định 90 ngày) và `details`.
  - *Module ghi nhận:* `app/audit.py` cung cấp hàm `log_audit_event()` ghi log độc lập vào `data/audit.jsonl` (đã nằm trong `.gitignore`), phân tách rạch ròi với logging nghiệp vụ của ứng dụng.
  - *Tích hợp Endpoint:* Đã tích hợp trực tiếp vào endpoint bật/tắt sự cố `/incidents/{name}/enable` và `/incidents/{name}/disable` trong `app/main.py`. Mọi hành động can thiệp sự cố đều được ghi nhận với đầy đủ trạng thái và actor.
  - *Công cụ truy vấn:* `scripts/query_audit.py` hỗ trợ truy vấn, trích xuất và lọc sự kiện kiểm toán theo `--action`, `--status`, `--limit`.
  - *Unit test:* Đã xây dựng `tests/test_audit.py` và kiểm thử tự động đạt 100% pass.
- **Lệnh thực thi truy vấn kiểm toán:**
  ```powershell
  python scripts/query_audit.py --limit 10
  ```
