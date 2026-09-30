# S-LI-U-KINH-DOANH-
LƯU TRỮ TOÀN BỘ CÁC SỐ LIỆU KINH DOANH CỦA RUBY KOI ĐỂ LÀM BÁO CÁO TÀI CHÍNH CHÍNH XÁC NHẤT CHO RUBY KOI, DỰA VÀO ĐÓ ĐỂ ĐÁNH GIÁ TÌNH HÌNH KINH DOANH, XÂY DỰNG DOANH NGHIỆP BỀN VỮNG & HIỆU QUẢ

---

## Agent Kế toán nội bộ Ruby Koi

Repo này chứa hai phần:

| Thành phần | Vị trí | Vai trò |
|---|---|---|
| **Agent** | `.claude/agents/ke-toan-noi-bo-ruby-koi.md` | Làm việc như một kế toán nội bộ. Agent tự lấy số trên Google Drive, nhập vào hệ thống, soát lỗi, lập báo cáo và nhắn chị Quyên. |
| **Bộ tính** | `ruby_koi_ketoan/` (Python) | Thực hiện mọi phép tính để con số luôn nhất quán và kiểm chứng được (có 27 bài kiểm thử). |
| Dữ liệu | `du_lieu/` | Các file CSV chuẩn, mở được bằng Excel/Google Sheets. Mô tả cột: `du_lieu/MO_TA_DU_LIEU.md` |
| Báo cáo | `bao_cao/ngay/`, `bao_cao/thang/` | Mỗi báo cáo có bản `.md` để đọc nhanh và bản `.xlsx` để lưu và đối chiếu. |
| Dữ liệu mẫu | `du_lieu_mau/` | 3 ngày số liệu giả lập để thử và kiểm thử phần kho. **Không phải số thật.** |

### Agent giải quyết 4 vấn đề

1. **Nhập – Xuất – Tồn – Hao hụt hằng ngày, quy ra tháng.** Tồn kho theo bình quân gia quyền. Công thức:
   *tồn lý thuyết = tồn đầu + nhập − bán theo định lượng − huỷ*. So với kiểm kê thực tế sẽ tách ra hao hụt
   **có lý do** (huỷ) và **không rõ lý do** (thất thoát). Nếu chỉ kiểm kê hàng tuần, chênh lệch dồn về lần kiểm
   sau, nên số tháng vẫn đúng.
2. **Kiểm soát hoá đơn mua bán.** Tách trả ngay và mua chịu. Theo dõi tuổi nợ từng NCC. Tự bắt các lỗi: sai
   thành tiền, đơn giá bất thường (ghi thiếu hàng nghìn), ghi trùng, giá mua lệch so với giá chuẩn, chi NVL trùng
   với khoản đang nợ (nghi là trả nợ bị ghi thành mua mới).
3. **Doanh thu từ POS.** Tự đọc sheet QTBH/SALES/PM của file DSR, tính doanh thu gộp đến thuần, khách nợ, cơ cấu
   tiền mặt/CK/thẻ, đối soát tiền mặt đếm với sổ, so với điểm hoà vốn và dự báo cuối tháng.
4. **Báo cáo đầy đủ mỗi ngày.** Gồm tóm tắt KPI, doanh thu, NXT, công nợ, P&L ngày và lũy kế, dòng tiền, danh
   sách cảnh báo xếp theo mức độ.

### Cách dùng

```bash
pip install -r requirements.txt

# Nhập số liệu gốc (chạy lại không bị nhân đôi)
python -m ruby_koi_ketoan nhap-dsr    RUBYKOI.DSR.T9.2026.xlsx --den-ngay 2026-09-29
python -m ruby_koi_ketoan nhap-so-quy SOQUYT9.2026.xlsx --thang 2026-09
python -m ruby_koi_ketoan nhap-ipos   ban_hang_theo_mon.xlsx --ngay 2026-09-29      # nếu có

# Soát lỗi và lập báo cáo
python -m ruby_koi_ketoan kiem-tra --den 2026-09-29
python -m ruby_koi_ketoan bao-cao-ngay  --ngay 2026-09-29 --in
python -m ruby_koi_ketoan bao-cao-thang --thang 2026-08 --in

# Thử trên dữ liệu mẫu
python -m ruby_koi_ketoan --du-lieu du_lieu_mau bao-cao-ngay --ngay 2026-10-03 --in
python -m pytest -q
```

Trong Claude Code, gọi agent bằng câu lệnh như: *"Dùng agent ke-toan-noi-bo-ruby-koi lập báo cáo ngày hôm qua"*.

### Cách tính (để đọc đúng con số)

- **Doanh thu thuần** = Doanh thu gộp − giảm giá/voucher − tiếp khách/chi chung/nội bộ − trừ lui.
  Khách nợ không bị trừ mà ghi vào **phải thu khách**.
- **Giá vốn** = Mua NVL (Sổ Quỹ cột Bếp/Bar + hàng mua chịu) + (Tồn đầu − Tồn cuối) của các NVL có theo dõi tồn.
  Sổ mua hàng chi tiết chỉ dùng cho số lượng nhập kho và soát giá, nhờ đó không bị cộng hai lần.
- **Mặt bằng (22 tr), BHXH (4,515 tr), khấu hao (103,3 tr)** được phân bổ đều theo ngày. Các con số này nằm trong
  `du_lieu/cau_hinh.json` và chị sửa được. **Trả ngân hàng 50 tr/tháng** chỉ xuất hiện ở dòng tiền.
- **Đúng kỳ:** lương tháng trước trả trong tháng này (ví dụ "lương bảo vệ T7" trả ngày 17/8) được tự nhận ra và
  loại khỏi lãi lỗ tháng này.
- **Thuế nộp và lãi vay** được ghi dưới EBITDA.

### Bảo mật số liệu

Repo này đang để **công khai (public)**. Vì vậy `du_lieu/` (trừ file mô tả) và `bao_cao/` bị `.gitignore` chặn,
không đưa lên GitHub. Nếu muốn dùng git để lưu trữ số thật, chị cần chuyển repo sang **Private** trước
(Settings → General → Danger Zone → Change visibility), sau đó mới bỏ chặn trong `.gitignore`.

Hướng dẫn cho nhân viên và lộ trình triển khai: xem `HUONG_DAN_VAN_HANH.md`.
