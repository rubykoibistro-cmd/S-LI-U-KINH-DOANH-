# Hướng dẫn vận hành – để số liệu kế toán Ruby Koi chính xác mỗi ngày

Agent chỉ chính xác khi số liệu đầu vào đủ. Dưới đây là **việc của từng người mỗi ngày** (tổng cộng mất
khoảng 10–15 phút) và **lộ trình 4 tuần** để đi từ làm thủ công sang báo cáo tự động.

## 1. Việc hằng ngày

| Ai | Khi nào | Việc | Ghi vào đâu |
|---|---|---|---|
| Thu ngân | Cuối mỗi ca | Chốt QTBH trên POS, điền đủ CA1 / CA2 / CK chị Quyên / TỔNG CỘNG / tiền phải nộp. **Không gõ đè lên ô công thức.** | DSR sheet QTBH |
| Thu ngân | Cuối ngày | Đếm két, ghi **số tiền mặt đếm thực tế** (sau khi đã chi trong ngày) | DSR sheet ĐẾM QUỸ hoặc gửi agent |
| Thu ngân | Mỗi lần chi | Mỗi phiếu chi ghi một dòng đúng cột nhóm. **Trả nợ NCC** ghi rõ "trả nợ + tên NCC + ngày hoá đơn", không ghi vào cột Bếp/Bar | Sổ Quỹ sheet ngày |
| Người đi chợ / nhận hàng | Khi nhận hàng | Ghi NCC, mặt hàng, **số lượng, đơn vị, đơn giá**, thành tiền, trả ngay hay nợ. Số lẻ ghi bằng dấu phẩy (2,5 kg) | Sổ mua hàng / sheet "sổ chi" |
| Bếp trưởng | Khi huỷ hàng | Ghi NVL, số lượng, lý do (ươn, hỏng, rơi, hết hạn, làm lại món) | `xuat_huy.csv` hoặc gửi agent |
| Quản lý | Sau khi đóng cửa | Xuất iPOS **"Báo cáo bán hàng theo mặt hàng"** của ngày, lưu vào Drive | thư mục DSR.2026 |
| Kho / Bếp | Cuối ngày (ít nhất Chủ nhật) | Cân, đếm 16 NVL giá trị cao (danh sách bên dưới) | `kiem_kho.csv` hoặc gửi agent |

## 2. Lộ trình 4 tuần

**Tuần 1: doanh thu và quỹ chính xác**
- Sửa các ô lỗi đã phát hiện trong DSR (xem file phát hiện ở mục 3).
- Bắt đầu ghi tiền mặt đếm thực tế mỗi ngày.
- Tải Sổ Quỹ T9 lên Drive để có lãi lỗ tháng 9.

**Tuần 2: công nợ sạch**
- Xác nhận các khoản nợ NCC còn treo mà báo cáo liệt kê.
- Từ nay mọi mua chịu phải có số chứng từ và hạn trả.

**Tuần 3: bắt đầu theo dõi tồn kho**
- Ngày 01/10 kiểm kê các NVL trong `du_lieu/danh_muc_nvl.csv` (16 NVL đề xuất). Chị cần xác nhận đơn vị tính và giá chuẩn.
- Ghi kết quả kiểm kê vào `du_lieu/ton_dau_ky.csv`.
- Kiểm kê lại mỗi Chủ nhật.

**Tuần 4: định lượng món**
- Lập `du_lieu/dinh_luong.csv` cho khoảng 20 món bán chạy nhất. Ví dụ: 1 phần bò lúc lắc dùng 0,15 kg lõi vai.
- Xuất iPOS theo món hằng ngày.
- Từ đây agent tách được **thất thoát không rõ lý do** cho từng NVL.

Nên làm theo cách "ít mà chắc": 16 NVL đầu tiên (bò, cá, tôm, mực, cừu, gà, heo, cà phê, dâu, kem, siro, trứng…)
chiếm phần lớn tiền mua nguyên liệu. Rau chợ mua dùng trong ngày không cần theo dõi tồn.

## 3. Số liệu thật & phát hiện

Danh mục NVL đề xuất (có giá mua thật), các lỗi đã phát hiện trong sổ gốc và các thông số cần xác nhận nằm trong
file riêng `PHAT_HIEN_SO_LIEU_T8_T9.md`. File này **không đưa lên GitHub** vì repo đang để công khai.
