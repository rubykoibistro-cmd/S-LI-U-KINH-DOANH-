# Mô tả các file dữ liệu

Cột có dấu * là bắt buộc.

## danh_muc_nvl.csv

Danh mục nguyên vật liệu. nhom: Bep | Bar | Tieu hao. quan_ly_ton: co (theo dõi tồn từng ngày) | khong (hàng chợ mua dùng ngay -> vào giá vốn ngày mua). ten_goi_khac: các tên ghi tay khác nhau, cách nhau bằng dấu |, ví dụ: bánh mỳ|bánh mì|banh mi.

Cột: `ma_nvl*`, `ten_nvl*`, `nhom`, `don_vi`, `don_gia_chuan`, `quan_ly_ton`, `ton_toi_thieu`, `nguong_hao_hut_pct`, `ncc_chinh`, `ten_goi_khac`

## dinh_luong.csv

Định lượng (BOM): 1 phần món ma_mon dùng bao nhiêu ma_nvl (theo don_vi của NVL).

Cột: `ma_mon*`, `ten_mon`, `ma_nvl*`, `luong*`

## ton_dau_ky.csv

Tồn kho đầu kỳ (kiểm kê chốt) tại ngày bắt đầu theo dõi.

Cột: `ngay*`, `ma_nvl*`, `so_luong*`, `don_gia`

## doanh_thu_ngay.csv

Quyết toán bán hàng (QTBH) từ POS/iPOS mỗi ngày. giam_gia = giảm giá NV + voucher + chiết khấu. tiep_khach_noi_bo = chi chung, tiếp khách, ăn nội bộ. cong_no_khach = khách nợ chưa trả (KHÔNG trừ khỏi doanh thu, chuyển sang phải thu). tien_mat = tiền mặt phải nộp theo POS (để trống sẽ tự tính). tien_mat_dem = tiền mặt thu ngân đếm thực tế cuối ca (đã trừ các khoản chi tiền mặt trong ngày).

Cột: `ngay*`, `doanh_thu_gop*`, `giam_gia`, `tiep_khach_noi_bo`, `tru_lui`, `cong_no_khach`, `chuyen_khoan`, `the`, `tien_mat`, `tien_mat_dem`, `so_khach`, `so_hoa_don`, `vat`, `ghi_chu`

## ban_hang_pos.csv

Số lượng từng món bán ra mỗi ngày (xuất từ iPOS: Báo cáo bán hàng theo mặt hàng).

Cột: `ngay*`, `ma_mon*`, `ten_mon`, `so_luong*`, `don_gia`, `thanh_tien`

## nhap_hang.csv

Hoá đơn/phiếu mua hàng. hinh_thuc_tt: tien_mat | chuyen_khoan | cong_no. Mua chịu (cong_no) sẽ tự vào sổ công nợ NCC.

Cột: `ngay*`, `so_chung_tu`, `ncc*`, `ma_nvl`, `ten_hang*`, `so_luong*`, `don_vi`, `don_gia`, `thanh_tien*`, `hinh_thuc_tt*`, `han_thanh_toan`, `nguoi_mua`, `ghi_chu`

## thanh_toan_ncc.csv

Các lần trả nợ nhà cung cấp. Có so_chung_tu thì trừ đúng hoá đơn đó, không có thì trừ hoá đơn cũ nhất của NCC trước.

Cột: `ngay*`, `ncc*`, `so_chung_tu`, `so_tien*`, `hinh_thuc_tt`, `ghi_chu`

## cong_no_ncc_dau_ky.csv

Công nợ NCC còn treo từ trước khi dùng hệ thống (ví dụ nợ tháng trước).

Cột: `ngay*`, `ncc*`, `so_chung_tu`, `so_tien*`, `han_thanh_toan`, `ghi_chu`

## chi_phi.csv

Chi phí vận hành (từ Sổ Quỹ). ky_phan_bo: tháng mà khoản chi thuộc về nếu khác tháng chi (vd lương T7 trả ngày 17/8 -> 2026-07). Nhóm: xem NHOM_CHI_PHI.

Cột: `ngay*`, `nhom_chi_phi*`, `noi_dung`, `so_tien*`, `hinh_thuc_tt`, `ky_phan_bo`, `ghi_chu`

## xuat_huy.csv

Hàng huỷ/hỏng/rơi vỡ/hết hạn được ghi nhận (hao hụt CÓ lý do).

Cột: `ngay*`, `ma_nvl*`, `so_luong*`, `ly_do`, `nguoi_ghi`

## kiem_kho.csv

Kiểm kê thực tế cuối ngày. Chênh lệch với tồn lý thuyết = hao hụt KHÔNG rõ lý do.

Cột: `ngay*`, `ma_nvl*`, `so_luong_thuc_te*`, `nguoi_kiem`

## thu_no_khach.csv

Thu tiền khách nợ (khách đoàn, công ty...).

Cột: `ngay*`, `khach_hang*`, `so_tien*`, `hinh_thuc_tt`, `ghi_chu`

## cong_no_khach_chi_tiet.csv

Chi tiết khách nợ phát sinh (tên khách). Tổng theo ngày nên khớp cột cong_no_khach.

Cột: `ngay*`, `khach_hang*`, `so_tien*`, `han_thu`, `ghi_chu`

## Nhóm chi phí (cột nhom_chi_phi trong chi_phi.csv)

- `luong`: Lương cố định
- `thoi_vu`: Lương thời vụ
- `bhxh`: Bảo hiểm xã hội
- `nvl_bep`: NVL Bếp (không qua sổ nhập hàng)
- `nvl_bar`: NVL Bar (không qua sổ nhập hàng)
- `vpp`: Văn phòng phẩm
- `marketing`: Marketing
- `dien_nuoc`: Điện nước
- `gas_da`: Gas, đá
- `tieu_hao`: Vật tư tiêu hao
- `bao_tri`: Bảo trì sửa chữa
- `decor_tiec`: Decor tiệc
- `tiep_khach`: Tiếp khách
- `do_cung_ship`: Đồ cúng, ship
- `ccdc`: Công cụ dụng cụ
- `mat_bang`: Thuê mặt bằng
- `thue_mrc`: Thuế / MRC
- `internet`: Internet
- `rac`: Rác
- `via_he`: Phí vỉa hè
- `phan_mem`: Phần mềm (POS...)
- `van_hanh_ho_koi`: Vận hành hồ cá Koi
- `rd_mon_moi`: R&D món mới
- `lai_vay`: Lãi vay ngân hàng
- `thue_nop`: Thuế nộp ngân sách
- `khac`: Chi phí khác
