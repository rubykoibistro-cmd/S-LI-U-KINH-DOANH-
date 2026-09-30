"""Định nghĩa các file dữ liệu chuẩn và nạp chúng vào bộ nhớ.

Mỗi nghiệp vụ có một file CSV (UTF-8) trong thư mục dữ liệu. Có thể mở/sửa bằng Excel
hoặc Google Sheets (File > Download > CSV). Cột nào không bắt buộc có thể để trống.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .tien_ich import chuan_hoa_ten, doc_ngay, doc_so

# Tên file -> (các cột, mô tả). Cột có dấu * là bắt buộc.
BANG = {
    "danh_muc_nvl.csv": (
        ["ma_nvl*", "ten_nvl*", "nhom", "don_vi", "don_gia_chuan", "quan_ly_ton",
         "ton_toi_thieu", "nguong_hao_hut_pct", "ncc_chinh", "ten_goi_khac"],
        "Danh mục nguyên vật liệu. nhom: Bep | Bar | Tieu hao. quan_ly_ton: co (theo dõi tồn "
        "từng ngày) | khong (hàng chợ mua dùng ngay -> vào giá vốn ngày mua). ten_goi_khac: các "
        "tên ghi tay khác nhau, cách nhau bằng dấu |, ví dụ: bánh mỳ|bánh mì|banh mi.",
    ),
    "dinh_luong.csv": (
        ["ma_mon*", "ten_mon", "ma_nvl*", "luong*"],
        "Định lượng (BOM): 1 phần món ma_mon dùng bao nhiêu ma_nvl (theo don_vi của NVL).",
    ),
    "ton_dau_ky.csv": (
        ["ngay*", "ma_nvl*", "so_luong*", "don_gia"],
        "Tồn kho đầu kỳ (kiểm kê chốt) tại ngày bắt đầu theo dõi.",
    ),
    "doanh_thu_ngay.csv": (
        ["ngay*", "doanh_thu_gop*", "giam_gia", "tiep_khach_noi_bo", "tru_lui", "cong_no_khach",
         "chuyen_khoan", "the", "tien_mat", "tien_mat_dem", "so_khach", "so_hoa_don", "vat",
         "ghi_chu"],
        "Quyết toán bán hàng (QTBH) từ POS/iPOS mỗi ngày. giam_gia = giảm giá NV + voucher + "
        "chiết khấu. tiep_khach_noi_bo = chi chung, tiếp khách, ăn nội bộ. cong_no_khach = khách "
        "nợ chưa trả (KHÔNG trừ khỏi doanh thu, chuyển sang phải thu). tien_mat = tiền mặt phải "
        "nộp theo POS (để trống sẽ tự tính). tien_mat_dem = tiền mặt thu ngân đếm thực tế cuối ca "
        "(đã trừ các khoản chi tiền mặt trong ngày).",
    ),
    "ban_hang_pos.csv": (
        ["ngay*", "ma_mon*", "ten_mon", "so_luong*", "don_gia", "thanh_tien"],
        "Số lượng từng món bán ra mỗi ngày (xuất từ iPOS: Báo cáo bán hàng theo mặt hàng).",
    ),
    "nhap_hang.csv": (
        ["ngay*", "so_chung_tu", "ncc*", "ma_nvl", "ten_hang*", "so_luong*", "don_vi", "don_gia",
         "thanh_tien*", "hinh_thuc_tt*", "han_thanh_toan", "nguoi_mua", "ghi_chu"],
        "Hoá đơn/phiếu mua hàng. hinh_thuc_tt: tien_mat | chuyen_khoan | cong_no. Mua chịu "
        "(cong_no) sẽ tự vào sổ công nợ NCC.",
    ),
    "thanh_toan_ncc.csv": (
        ["ngay*", "ncc*", "so_chung_tu", "so_tien*", "hinh_thuc_tt", "ghi_chu"],
        "Các lần trả nợ nhà cung cấp. Có so_chung_tu thì trừ đúng hoá đơn đó, không có thì trừ "
        "hoá đơn cũ nhất của NCC trước.",
    ),
    "cong_no_ncc_dau_ky.csv": (
        ["ngay*", "ncc*", "so_chung_tu", "so_tien*", "han_thanh_toan", "ghi_chu"],
        "Công nợ NCC còn treo từ trước khi dùng hệ thống (ví dụ nợ tháng trước).",
    ),
    "chi_phi.csv": (
        ["ngay*", "nhom_chi_phi*", "noi_dung", "so_tien*", "hinh_thuc_tt", "ky_phan_bo", "ghi_chu"],
        "Chi phí vận hành (từ Sổ Quỹ). ky_phan_bo: tháng mà khoản chi thuộc về nếu khác tháng "
        "chi (vd lương T7 trả ngày 17/8 -> 2026-07). Nhóm: xem NHOM_CHI_PHI.",
    ),
    "xuat_huy.csv": (
        ["ngay*", "ma_nvl*", "so_luong*", "ly_do", "nguoi_ghi"],
        "Hàng huỷ/hỏng/rơi vỡ/hết hạn được ghi nhận (hao hụt CÓ lý do).",
    ),
    "kiem_kho.csv": (
        ["ngay*", "ma_nvl*", "so_luong_thuc_te*", "nguoi_kiem"],
        "Kiểm kê thực tế cuối ngày. Chênh lệch với tồn lý thuyết = hao hụt KHÔNG rõ lý do.",
    ),
    "thu_no_khach.csv": (
        ["ngay*", "khach_hang*", "so_tien*", "hinh_thuc_tt", "ghi_chu"],
        "Thu tiền khách nợ (khách đoàn, công ty...).",
    ),
    "cong_no_khach_chi_tiet.csv": (
        ["ngay*", "khach_hang*", "so_tien*", "han_thu", "ghi_chu"],
        "Chi tiết khách nợ phát sinh (tên khách). Tổng theo ngày nên khớp cột cong_no_khach.",
    ),
}

NHOM_CHI_PHI = {
    "luong": "Lương cố định",
    "thoi_vu": "Lương thời vụ",
    "bhxh": "Bảo hiểm xã hội",
    "nvl_bep": "NVL Bếp (không qua sổ nhập hàng)",
    "nvl_bar": "NVL Bar (không qua sổ nhập hàng)",
    "vpp": "Văn phòng phẩm",
    "marketing": "Marketing",
    "dien_nuoc": "Điện nước",
    "gas_da": "Gas, đá",
    "tieu_hao": "Vật tư tiêu hao",
    "bao_tri": "Bảo trì sửa chữa",
    "decor_tiec": "Decor tiệc",
    "tiep_khach": "Tiếp khách",
    "do_cung_ship": "Đồ cúng, ship",
    "ccdc": "Công cụ dụng cụ",
    "mat_bang": "Thuê mặt bằng",
    "thue_mrc": "Thuế / MRC",
    "internet": "Internet",
    "rac": "Rác",
    "via_he": "Phí vỉa hè",
    "phan_mem": "Phần mềm (POS...)",
    "van_hanh_ho_koi": "Vận hành hồ cá Koi",
    "rd_mon_moi": "R&D món mới",
    "lai_vay": "Lãi vay ngân hàng",
    "thue_nop": "Thuế nộp ngân sách",
    "khac": "Chi phí khác",
}
# Nhóm tính vào giá vốn (COGS) chứ không phải chi phí vận hành.
NHOM_GIA_VON = {"nvl_bep", "nvl_bar"}
# Nhóm không vào lãi/lỗ hoạt động (ghi riêng dưới EBITDA).
NHOM_TAI_CHINH = {"lai_vay", "thue_nop"}

CAU_HINH_MAC_DINH = {  # số thật của nhà hàng đặt trong <du_lieu>/cau_hinh.json
    "ten_nha_hang": "RUBY KOI BISTRO",
    "so_ghe": 0,
    "chi_phi_co_dinh_thang": {  # {nhom: {"so_tien": ..., "ghi_chu": ...}} – phân bổ đều theo ngày
        "mat_bang": {"so_tien": 0, "ghi_chu": "Thuê mặt bằng / tháng"},
        "bhxh": {"so_tien": 0, "ghi_chu": "BHXH / tháng"},
    },
    "khau_hao_thang": 0,
    "tra_ngan_hang_thang": 0,
    "muc_tieu_doanh_thu_thang": 0,
    "doanh_thu_hoa_von_thang": 0,
    "so_ngay_no_ncc_mac_dinh": 7,
    # so_quy: tiền mua NVL lấy từ Sổ Quỹ (cột Bếp/Bar) + hàng mua chịu; sổ nhập hàng chi tiết chỉ
    #         dùng cho số lượng nhập kho & soát giá.  nhap_hang: sổ nhập hàng là nguồn tiền mua NVL.
    "nguon_mua_nvl": "so_quy",
    "nguong": {
        "food_cost_pct_toi_da": 0.30,
        "hao_hut_pct_canh_bao": 0.03,
        "hao_hut_pct_nghiem_trong": 0.05,
        "lech_gia_mua_pct": 0.10,
        "gia_tri_dong_canh_bao_gia": 200000,
        "lech_quy_tien_mat": 50000,
        "lech_pos_vs_qtbh_pct": 0.01,
        "lech_thanh_tien_dong": 1000,
    },
}


@dataclass
class DuLieu:
    thu_muc: Path
    cau_hinh: dict
    bang: dict[str, list[dict]] = field(default_factory=dict)
    loi_nap: list[str] = field(default_factory=list)

    def __getitem__(self, ten: str) -> list[dict]:
        return self.bang.get(ten, [])

    # ---- Tra cứu danh mục ----
    def nvl(self, ma: str) -> dict | None:
        return self._nvl_theo_ma.get(ma)

    def tim_nvl_theo_ten(self, ten: str) -> dict | None:
        return self._nvl_theo_ten.get(chuan_hoa_ten(ten))

    def xay_chi_muc(self) -> None:
        self._nvl_theo_ma = {}
        self._nvl_theo_ten = {}
        for d in self["danh_muc_nvl.csv"]:
            self._nvl_theo_ma[d["ma_nvl"]] = d
            ten_list = [d["ten_nvl"], d["ma_nvl"]] + (d.get("ten_goi_khac") or "").split("|")
            for t in ten_list:
                if t and t.strip():
                    self._nvl_theo_ten.setdefault(chuan_hoa_ten(t), d)
        self.dinh_luong: dict[str, list[tuple[str, float]]] = {}
        for d in self["dinh_luong.csv"]:
            self.dinh_luong.setdefault(d["ma_mon"], []).append((d["ma_nvl"], d["luong"]))

    def nguong(self, ten: str) -> float:
        return self.cau_hinh["nguong"][ten]


_COT_SO = {
    "don_gia_chuan", "ton_toi_thieu", "nguong_hao_hut_pct", "luong", "so_luong", "don_gia",
    "doanh_thu_gop", "giam_gia", "tiep_khach_noi_bo", "tru_lui", "cong_no_khach", "chuyen_khoan",
    "the", "tien_mat", "tien_mat_dem", "so_khach", "so_hoa_don", "vat", "thanh_tien", "so_tien",
    "so_luong_thuc_te",
}
_COT_SO_LUONG = {"luong", "so_luong", "so_luong_thuc_te", "ton_toi_thieu"}
_COT_NGAY = {"ngay", "han_thanh_toan", "han_thu"}
# Các cột số để trống nghĩa là "chưa có dữ liệu" (khác với 0).
_COT_CO_THE_TRONG = {"tien_mat", "tien_mat_dem", "so_khach", "so_hoa_don", "don_gia",
                     "thanh_tien", "don_gia_chuan", "nguong_hao_hut_pct", "vat"}


def _gop_cau_hinh(goc: dict, them: dict) -> dict:
    kq = dict(goc)
    for k, v in them.items():
        if isinstance(v, dict) and isinstance(kq.get(k), dict):
            kq[k] = _gop_cau_hinh(kq[k], v)
        else:
            kq[k] = v
    return kq


def nap_du_lieu(thu_muc: str | Path) -> DuLieu:
    thu_muc = Path(thu_muc)
    cau_hinh = dict(CAU_HINH_MAC_DINH)
    tep_cau_hinh = thu_muc / "cau_hinh.json"
    if tep_cau_hinh.exists():
        cau_hinh = _gop_cau_hinh(cau_hinh, json.loads(tep_cau_hinh.read_text(encoding="utf-8")))
    dl = DuLieu(thu_muc=thu_muc, cau_hinh=cau_hinh)
    for ten, (cot, _) in BANG.items():
        tep = thu_muc / ten
        dl.bang[ten] = _doc_csv(tep, cot, dl.loi_nap) if tep.exists() else []
    dl.xay_chi_muc()
    return dl


def _doc_csv(tep: Path, cot: list[str], loi: list[str]) -> list[dict]:
    bat_buoc = [c.rstrip("*") for c in cot if c.endswith("*")]
    ds = []
    with tep.open(encoding="utf-8-sig", newline="") as f:
        for so_dong, hang in enumerate(csv.DictReader(f), start=2):
            hang = {(k or "").strip(): (v or "").strip() for k, v in hang.items()}
            if not any(hang.values()):
                continue
            thieu = [c for c in bat_buoc if not hang.get(c)]
            if thieu:
                loi.append(f"{tep.name} dòng {so_dong}: thiếu cột bắt buộc {', '.join(thieu)} -> bỏ qua")
                continue
            ban_ghi = {"_dong": so_dong}
            for k, v in hang.items():
                if k in _COT_NGAY:
                    ngay = doc_ngay(v)
                    if v and ngay is None:
                        loi.append(f"{tep.name} dòng {so_dong}: không đọc được ngày '{v}' ở cột {k}")
                    ban_ghi[k] = ngay
                elif k in _COT_SO:
                    ban_ghi[k] = (None if (v == "" and k in _COT_CO_THE_TRONG)
                                  else doc_so(v, so_luong=k in _COT_SO_LUONG))
                else:
                    ban_ghi[k] = v
            if "ngay" in ban_ghi and ban_ghi["ngay"] is None:
                continue
            ds.append(ban_ghi)
    return ds


def tao_mau(thu_muc: str | Path, ghi_de: bool = False) -> list[Path]:
    """Tạo các file CSV trống đúng cột + file cấu hình + file mô tả."""
    thu_muc = Path(thu_muc)
    thu_muc.mkdir(parents=True, exist_ok=True)
    da_tao = []
    for ten, (cot, _) in BANG.items():
        tep = thu_muc / ten
        if tep.exists() and not ghi_de:
            continue
        with tep.open("w", encoding="utf-8-sig", newline="") as f:
            csv.writer(f).writerow([c.rstrip("*") for c in cot])
        da_tao.append(tep)
    tep_ch = thu_muc / "cau_hinh.json"
    if not tep_ch.exists() or ghi_de:
        tep_ch.write_text(json.dumps(CAU_HINH_MAC_DINH, ensure_ascii=False, indent=2), encoding="utf-8")
        da_tao.append(tep_ch)
    return da_tao


def mo_ta_bang() -> str:
    dong = ["# Mô tả các file dữ liệu\n", "Cột có dấu * là bắt buộc.\n"]
    for ten, (cot, mo_ta) in BANG.items():
        dong.append(f"## {ten}\n\n{mo_ta}\n\nCột: `{'`, `'.join(cot)}`\n")
    dong.append("## Nhóm chi phí (cột nhom_chi_phi trong chi_phi.csv)\n")
    dong += [f"- `{k}`: {v}" for k, v in NHOM_CHI_PHI.items()]
    return "\n".join(dong) + "\n"


def trong_khoang(ds: list[dict], tu: date, den: date, cot: str = "ngay") -> list[dict]:
    return [r for r in ds if r.get(cot) and tu <= r[cot] <= den]
