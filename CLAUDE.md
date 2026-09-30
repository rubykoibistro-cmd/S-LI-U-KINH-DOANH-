# Ruby Koi – Số liệu kinh doanh & Kế toán nội bộ

- Việc kế toán (báo cáo ngày/tháng, kho, công nợ, doanh thu, lãi lỗ) giao cho agent `ke-toan-noi-bo-ruby-koi`
  (`.claude/agents/ke-toan-noi-bo-ruby-koi.md`) – làm đúng quy trình và nguyên tắc chính xác trong đó.
- Mọi phép tính đi qua bộ `ruby_koi_ketoan` (`python -m ruby_koi_ketoan -h`); không tự tính tay số đưa vào báo cáo.
- Dữ liệu chuẩn ở `du_lieu/` (mô tả cột: `du_lieu/MO_TA_DU_LIEU.md`); báo cáo ở `bao_cao/`. `du_lieu_mau/` là số giả lập.
- File gốc tải từ Drive để ở scratchpad, không commit. Không sửa file gốc trên Drive khi chưa được chị Quyên đồng ý.
- Trước khi commit thay đổi code: `python -m pytest -q` phải xanh.
- Người nhận báo cáo: chị Quyên. Xưng "em", viết tiếng Việt, số trước – nhận định sau.
