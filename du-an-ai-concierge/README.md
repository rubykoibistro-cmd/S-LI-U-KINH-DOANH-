# Dự án: AI Concierge Chăm sóc Sức khoẻ – Sắc đẹp – Phong thái

> Mô hình kinh doanh độc bản: thay thế hành trình "khách hàng phải đến 3 nơi (spa/thẩm mỹ viện, phòng gym, lớp học phong thái)" bằng **một hệ sinh thái Agent AI cá nhân hoá**, đồng hành 24/7, kết nối đa thương hiệu uy tín, có điểm chạm vật lý định kỳ để giữ chất lượng và lòng tin.

## Cấu trúc thư mục

| File | Nội dung |
|---|---|
| [`01-MO-HINH-KINH-DOANH.md`](./01-MO-HINH-KINH-DOANH.md) | Cố vấn mô hình kinh doanh: insight, mô hình độc bản, dòng doanh thu, lợi thế cạnh tranh, rủi ro pháp lý |
| [`02-KIEN-TRUC-AGENT-AI.md`](./02-KIEN-TRUC-AGENT-AI.md) | Kiến trúc kỹ thuật hệ multi-agent (Agent Boss + các agent chuyên môn), luồng dữ liệu, đề xuất công nghệ |
| [`03-LO-TRINH-TRIEN-KHAI.md`](./03-LO-TRINH-TRIEN-KHAI.md) | Lộ trình triển khai theo giai đoạn (MVP → mở rộng → nền tảng B2B2C) |
| [`agents/`](./agents) | Bản thiết kế "persona" (system prompt nền) cho từng agent — dùng làm tài liệu gốc khi triển khai kỹ thuật thật (Claude Agent SDK hoặc nền tảng tương đương) |

## Tóm tắt 30 giây

- **Vấn đề**: khách hàng làm đẹp/chăm sóc sức khoẻ hiện phải tự ghép nối 3 nguồn: spa (da), gym (dáng), lớp học (phong thái) — rời rạc, tốn thời gian, thiếu người đồng hành liên tục giữa các lần đến.
- **Giải pháp độc bản**: **Agent Boss** — một trợ lý AI riêng cho từng khách hàng — điều phối các agent chuyên môn (da liễu, PT, phong thái, cố vấn sản phẩm) dựa trên **một hồ sơ sức khoẻ – sắc đẹp 360°** duy nhất, đồng hành hằng ngày, chỉ chạm điểm vật lý khi cần đo đạc/thực hiện dịch vụ tay nghề.
- **Khác biệt lớn nhất**: nền tảng không chỉ bán sản phẩm của Ruby Koi (Skincode, Skinshort, kem body...) mà đóng vai trò **"cố vấn độc lập đa thương hiệu"** — agent bác sĩ được quyền đề xuất sản phẩm đối tác khi sản phẩm nhà không phù hợp (dị ứng, ngân sách, mục tiêu khác) → tăng lòng tin tuyệt đối, biến nền tảng thành **hệ điều hành ngành làm đẹp – sức khoẻ cá nhân hoá**, không phải một cửa hàng.
