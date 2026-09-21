# Kiến trúc kỹ thuật: Hệ Multi-Agent "Agent Boss"

*Tài liệu kỹ thuật — bản thiết kế nền để đội dev / Claude Agent SDK triển khai*

---

## 1. Nguyên tắc thiết kế

1. **Một danh tính duy nhất trước khách hàng**: dù có 5-6 agent chuyên môn phía sau, khách hàng chỉ trò chuyện với **một Agent Boss** — giống một "concierge cá nhân" duy nhất. Các agent chuyên môn là *nội bộ* (subagents), không lộ diện trực tiếp trừ khi cần trích dẫn ý kiến chuyên gia ("Bác sĩ da liễu của hệ thống ghi nhận...").
2. **Hồ sơ 360° làm trung tâm**: mọi agent đọc/ghi vào cùng một **Customer Profile Store** — tránh tình trạng "phải kể lại từ đầu".
3. **Con người thật luôn ở vòng kiểm duyệt (human-in-the-loop) cho quyết định rủi ro cao**: chẩn đoán bất thường, dị ứng nghiêm trọng, thay đổi phác đồ lớn → escalate cho bác sĩ/chuyên gia thật duyệt trước khi Agent Boss truyền đạt lại cho khách.
4. **Không spam**: agent chỉ chủ động nhắn theo **lịch trình đã cá nhân hoá** (routine nhắc uống nước/bôi kem/tập luyện) hoặc khi có **sự kiện quan trọng** (kết quả đo mới, cảnh báo tương tác sản phẩm) — có giới hạn tần suất tối đa/ngày do khách tự cấu hình.
5. **Minh bạch nguồn gốc đề xuất**: mọi đề xuất sản phẩm ghi rõ agent nào đưa ra, dựa trên dữ liệu nào, có phải đối tác trả hoa hồng không.

---

## 2. Sơ đồ hệ thống

```
┌──────────────────────────── Kênh giao tiếp khách hàng ────────────────────────────┐
│   App/Web chat · Zalo OA · WhatsApp · (tương lai: voice)                          │
└───────────────────────────────────┬────────────────────────────────────────────────┘
                                     ▼
                        ┌────────────────────────┐
                        │      AGENT BOSS         │  ← Orchestrator chính
                        │  (Router + Memory +     │     (system prompt: agents/agent-boss.md)
                        │   Nhân cách nhất quán)  │
                        └────────────┬────────────┘
             ┌───────────┬───────────┼───────────┬─────────────┐
             ▼           ▼           ▼           ▼             ▼
      Agent Bác sĩ   Agent PT    Agent Phong  Agent Cố vấn  Agent CSKH/
      Da liễu &      Thể hình &  thái & Hình  Sản phẩm &    Vận hành
      Sắc đẹp        Dinh dưỡng  ảnh cá nhân  Đa thương hiệu (booking, đơn hàng,
                                                              thanh toán, giao vận)
             │           │           │           │             │
             └───────────┴─────┬─────┴───────────┴─────────────┘
                                ▼
                  ┌─────────────────────────────┐
                  │   CUSTOMER PROFILE STORE     │  Hồ sơ 360°: da, dáng, phong thái,
                  │   (hồ sơ 360° + lịch sử)     │  dị ứng, mục tiêu, lịch sử sản phẩm,
                  └──────────────┬───────────────┘  kết quả đo, ngân sách, tần suất OK
                                 │
                  ┌──────────────┴───────────────┐
                  ▼                               ▼
     ┌────────────────────────┐      ┌──────────────────────────────┐
     │  FORMULARY DATABASE     │      │  HUMAN-IN-THE-LOOP LAYER      │
     │  (sản phẩm nhà + đối    │      │  Bác sĩ da liễu / chuyên gia  │
     │  tác, thành phần, chỉ   │      │  dinh dưỡng thật review/duyệt│
     │  định, chống chỉ định)  │      │  các case rủi ro cao          │
     └────────────────────────┘      └──────────────────────────────┘
                                 │
                  ┌──────────────┴───────────────┐
                  ▼                               ▼
     ĐIỂM CHẠM VẬT LÝ (booking/CRM spa-gym)   BRAND ĐỐI TÁC (API/EDI đặt hàng,
                                                đối soát hoa hồng)
```

---

## 3. Vai trò từng Agent (chi tiết persona ở thư mục `agents/`)

| Agent | Nhiệm vụ chính | Input | Output |
|---|---|---|---|
| **Agent Boss** | Điều phối, giữ mạch hội thoại, tổng hợp câu trả lời từ các agent chuyên môn thành 1 giọng nói duy nhất, quản lý tần suất liên hệ | Tin nhắn khách, hồ sơ 360°, kết quả từ subagents | Phản hồi tự nhiên, nhắc nhở đúng lúc |
| **Agent Bác sĩ Da liễu & Sắc đẹp** | Phân tích tình trạng da (ảnh, mô tả, chỉ số đo tại spa), theo dõi tiến trình, đề xuất routine, cảnh báo dị ứng/tương tác | Ảnh da, chỉ số đo, lịch sử sản phẩm | Routine chăm da, cảnh báo, khi cần → escalate bác sĩ thật |
| **Agent PT Thể hình & Dinh dưỡng** | Lộ trình tập luyện + dinh dưỡng theo mục tiêu (giảm cân/tăng cơ/dáng), theo dõi số đo | Số đo cơ thể, mục tiêu, tần suất tập | Lịch tập, thực đơn gợi ý, nhắc lịch |
| **Agent Phong thái & Hình ảnh cá nhân** | Tư vấn giao tiếp, dáng đứng/đi, phong cách trang phục, sự tự tin (qua chat + video review định kỳ) | Video/ảnh khách gửi, mục tiêu (phỏng vấn, sự kiện, đời sống) | Bài tập phong thái, phản hồi cải thiện |
| **Agent Cố vấn Sản phẩm & Đa thương hiệu** | Matching nhu cầu ↔ Formulary Database (hàng nhà ưu tiên, đối tác khi phù hợp hơn), giải thích minh bạch lý do đề xuất | Hồ sơ khách, Formulary Database | Đề xuất sản phẩm kèm lý do + disclosure hoa hồng nếu có |
| **Agent CSKH/Vận hành** | Đặt lịch spa/gym/coaching, xử lý đơn hàng, giao vận, thanh toán, thu thập phản hồi | Yêu cầu khách, lịch trống đối tác | Xác nhận lịch/đơn hàng, cập nhật hồ sơ |

---

## 4. Đề xuất công nghệ (giai đoạn MVP)

> Mục tiêu: chi phí thấp, triển khai nhanh, dễ thay thế từng phần khi mở rộng.

- **Orchestration**: Claude Agent SDK (Anthropic) — Agent Boss là orchestrator gọi các subagent chuyên môn qua tool-calling; mỗi subagent = 1 system prompt + bộ "tool" riêng (đọc hồ sơ, tra Formulary, đặt lịch).
- **Kênh giao tiếp khách hàng (VN)**: Zalo OA (phổ biến nhất tại VN) + web chat; cân nhắc WhatsApp Business cho khách nước ngoài/cao cấp.
- **Customer Profile Store**: cơ sở dữ liệu có trường có cấu trúc (da, số đo, dị ứng...) + vector store cho ghi chú tự do/ảnh (để agent "nhớ ngữ cảnh").
- **Formulary Database**: bảng sản phẩm (nhà + đối tác) gắn thành phần, chỉ định/chống chỉ định, nguồn gốc, % hoa hồng đối tác — là "nguồn sự thật" để Agent Cố vấn tra cứu, tránh AI "bịa" thông tin sản phẩm.
- **CRM/Booking tích hợp**: kết nối lịch flagship spa + đối tác gym/coaching (Google Calendar/CRM lịch spa sẵn có nếu Ruby Koi đang dùng).
- **Human-in-the-loop**: dashboard nội bộ cho bác sĩ/chuyên gia thật duyệt các case được agent gắn cờ rủi ro cao, trước khi Agent Boss phản hồi khách.
- **Bảo mật**: mã hoá dữ liệu nhạy cảm (ảnh da, sức khoẻ), phân quyền truy cập theo vai trò, quy trình xin đồng ý & xoá dữ liệu theo yêu cầu (đáp ứng Nghị định 13/2023/NĐ-CP).

---

## 5. Vòng đời một khách hàng (customer journey kỹ thuật)

1. **Onboarding**: khách điền bộ câu hỏi (mục tiêu, dị ứng, ngân sách) + đến flagship đo da/dáng lần đầu (hoặc gửi ảnh/chỉ số tự đo) → tạo hồ sơ 360° ban đầu.
2. **Agent Boss** giới thiệu bản thân, đặt kỳ vọng đúng (đồng hành AI, không thay thế bác sĩ), hỏi tần suất liên hệ mong muốn.
3. **Routine hằng ngày**: nhắc chăm da/uống Skinshort/tập luyện theo lịch cá nhân hoá — khách phản hồi/log kết quả.
4. **Định kỳ (2-4 tuần)**: Agent Boss chủ động tổng hợp tiến trình, đề xuất điều chỉnh (kèm Agent chuyên môn liên quan), nhắc lịch đến flagship/gym để đo lại.
5. **Khi có bất thường** (dị ứng, không đạt tiến độ): Agent gắn cờ → escalate chuyên gia thật → Agent Boss truyền đạt lại hướng xử lý đã được duyệt.
6. **Upsell tự nhiên**: khi hồ sơ cho thấy nhu cầu mới (vd: sắp có sự kiện quan trọng → cần coaching phong thái gấp), Agent Boss chủ động gợi ý nâng gói/dịch vụ liên quan — đúng lúc, đúng nhu cầu, không spam.

---

## 6. Chỉ số cần theo dõi (KPI kỹ thuật & kinh doanh)

- Tỷ lệ khách hàng hoạt động hằng tuần (WAU/khách subscription).
- Retention theo cohort (chỉ số quan trọng nhất — chứng minh giá trị "đồng hành").
- Tỷ lệ đề xuất sản phẩm được khách chấp nhận (conversion), tách riêng hàng nhà vs đối tác.
- Số ca escalate lên chuyên gia thật / tổng tương tác (theo dõi rủi ro & khối lượng công việc chuyên gia).
- NPS/độ hài lòng theo từng agent chuyên môn (da/dáng/phong thái riêng biệt).
- Doanh thu theo từng dòng (subscription, bán hàng nhà, hoa hồng đối tác, dịch vụ vật lý).
