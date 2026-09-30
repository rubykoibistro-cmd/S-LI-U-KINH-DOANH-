"""Kiểm soát hoá đơn mua hàng, công nợ nhà cung cấp và công nợ khách hàng."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

from .du_lieu import DuLieu, trong_khoang
from .tien_ich import chuan_hoa_ten, dinh_dang_so, dinh_dang_tien

HINH_THUC = {"tien_mat": "Tiền mặt", "chuyen_khoan": "Chuyển khoản", "cong_no": "Công nợ", "the": "Thẻ"}


def chuan_hinh_thuc(s: str) -> str:
    s = chuan_hoa_ten(s)
    if s in ("cong no", "cong_no", "no", "chiu", "mua chiu", "cn"):
        return "cong_no"
    if s in ("chuyen khoan", "ck", "bank", "ngan hang"):
        return "chuyen_khoan"
    if s in ("the", "visa", "pos"):
        return "the"
    return "tien_mat"


@dataclass
class HoaDon:
    ncc: str
    so_chung_tu: str
    ngay: date
    han: date
    so_tien: float
    da_tra: float = 0.0
    dau_ky: bool = False
    ghi_chu: str = ""

    @property
    def con_lai(self) -> float:
        return round(self.so_tien - self.da_tra, 2)


@dataclass
class KetQuaCongNo:
    ngay_chot: date
    hoa_don: list[HoaDon] = field(default_factory=list)
    tra_thua: list[dict] = field(default_factory=list)
    canh_bao: list[dict] = field(default_factory=list)

    def con_no(self) -> list[HoaDon]:
        return [h for h in self.hoa_don if h.con_lai > 0.5]

    def tuoi_no(self) -> dict[str, dict[str, float]]:
        """Phân tích tuổi nợ theo NCC: chưa đến hạn | quá hạn 1-7 | 8-30 | >30 ngày."""
        kq: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for h in self.con_no():
            qua = (self.ngay_chot - h.han).days
            nhom = ("chua_den_han" if qua <= 0 else "qua_han_1_7" if qua <= 7
                    else "qua_han_8_30" if qua <= 30 else "qua_han_tren_30")
            kq[h.ncc][nhom] += h.con_lai
            kq[h.ncc]["tong"] += h.con_lai
        return kq

    def tong_con_no(self) -> float:
        return sum(h.con_lai for h in self.con_no())


def tinh_cong_no_ncc(dl: DuLieu, ngay_chot: date) -> KetQuaCongNo:
    kq = KetQuaCongNo(ngay_chot=ngay_chot)
    so_ngay_no = int(dl.cau_hinh.get("so_ngay_no_ncc_mac_dinh", 7))

    for r in dl["cong_no_ncc_dau_ky.csv"]:
        if r["ngay"] > ngay_chot:
            continue
        kq.hoa_don.append(HoaDon(ncc=r["ncc"], so_chung_tu=r.get("so_chung_tu", ""), ngay=r["ngay"],
                                 han=r.get("han_thanh_toan") or r["ngay"] + timedelta(days=so_ngay_no),
                                 so_tien=r["so_tien"], dau_ky=True, ghi_chu=r.get("ghi_chu", "")))

    gom: dict[tuple, HoaDon] = {}
    for r in dl["nhap_hang.csv"]:
        if r["ngay"] > ngay_chot or chuan_hinh_thuc(r.get("hinh_thuc_tt", "")) != "cong_no":
            continue
        ct = r.get("so_chung_tu") or f"{r['ngay'].isoformat()}"
        khoa = (chuan_hoa_ten(r["ncc"]), ct)
        tien = r["thanh_tien"] if r["thanh_tien"] is not None else r["so_luong"] * (r["don_gia"] or 0)
        if khoa not in gom:
            gom[khoa] = HoaDon(ncc=r["ncc"], so_chung_tu=ct, ngay=r["ngay"],
                               han=r.get("han_thanh_toan") or r["ngay"] + timedelta(days=so_ngay_no),
                               so_tien=0.0)
        gom[khoa].so_tien += tien
    kq.hoa_don.extend(gom.values())
    kq.hoa_don.sort(key=lambda h: (h.ngay, h.ncc))

    for tt in sorted(dl["thanh_toan_ncc.csv"], key=lambda r: r["ngay"]):
        if tt["ngay"] > ngay_chot:
            continue
        con = tt["so_tien"]
        ncc = chuan_hoa_ten(tt["ncc"])
        cua_ncc = [h for h in kq.hoa_don if chuan_hoa_ten(h.ncc) == ncc and h.con_lai > 0.5]
        if tt.get("so_chung_tu"):
            dung = [h for h in cua_ncc if h.so_chung_tu == tt["so_chung_tu"]]
            cua_ncc = dung + [h for h in cua_ncc if h not in dung]
        for h in cua_ncc:
            if con <= 0.5:
                break
            tra = min(con, h.con_lai)
            h.da_tra += tra
            con -= tra
        if con > 0.5:
            kq.tra_thua.append({**tt, "so_tien_thua": con})
            kq.canh_bao.append({"muc": "cao", "loai": "Công nợ NCC", "ngay": tt["ngay"],
                                "noi_dung": f"Trả {tt['ncc']} {dinh_dang_tien(tt['so_tien'])}đ nhưng sổ chỉ "
                                            f"còn nợ {dinh_dang_tien(tt['so_tien'] - con)}đ – thừa "
                                            f"{dinh_dang_tien(con)}đ: thiếu hoá đơn nợ gốc hoặc trả trùng"})

    for h in kq.con_no():
        qua = (ngay_chot - h.han).days
        if qua > 0:
            kq.canh_bao.append({"muc": "cao" if qua > 30 else "trung_binh", "loai": "Công nợ NCC",
                                "ngay": ngay_chot,
                                "noi_dung": f"{h.ncc} ({h.so_chung_tu}, {h.ngay:%d/%m}): còn nợ "
                                            f"{dinh_dang_tien(h.con_lai)}đ, quá hạn {qua} ngày"})
    return kq


def kiem_soat_hoa_don(dl: DuLieu, tu: date, den: date) -> list[dict]:
    """Soát lỗi hoá đơn mua: sai phép nhân, trùng, lệch giá, thiếu thông tin."""
    cb: list[dict] = []
    lech_cho_phep = dl.nguong("lech_thanh_tien_dong")
    nguong_gia = dl.nguong("lech_gia_mua_pct")
    ds = sorted(dl["nhap_hang.csv"], key=lambda r: (r["ngay"], r["_dong"]))

    gia_gan_nhat: dict[str, float] = {}
    da_thay: dict[tuple, int] = {}
    for r in ds:
        trong_ky = tu <= r["ngay"] <= den
        nvl = dl.nvl(r["ma_nvl"]) if r.get("ma_nvl") else dl.tim_nvl_theo_ten(r["ten_hang"])
        khoa_gia = nvl["ma_nvl"] if nvl else chuan_hoa_ten(r["ten_hang"])
        dg = r.get("don_gia")
        if dg is None and r["so_luong"]:
            dg = (r["thanh_tien"] or 0) / r["so_luong"]
        if trong_ky:
            vi_tri = f"dòng {r['_dong']} ({r['ngay']:%d/%m} {r['ncc']} – {r['ten_hang']})"
            if r.get("don_gia") is not None and r["thanh_tien"] is not None:
                dung = r["so_luong"] * r["don_gia"]
                if abs(dung - r["thanh_tien"]) > lech_cho_phep:
                    cb.append({"muc": "cao", "loai": "Hoá đơn", "ngay": r["ngay"],
                               "noi_dung": f"Sai thành tiền {vi_tri}: {dinh_dang_so(r['so_luong'])} × "
                                           f"{dinh_dang_tien(r['don_gia'])} = {dinh_dang_tien(dung)} nhưng ghi "
                                           f"{dinh_dang_tien(r['thanh_tien'])}"})
            if dg is not None and 0 < dg < 500:
                cb.append({"muc": "cao", "loai": "Hoá đơn", "ngay": r["ngay"],
                           "noi_dung": f"Đơn giá bất thường {dinh_dang_so(dg)}đ ở {vi_tri} – nghi ghi thiếu "
                                       "hàng nghìn (vd 16,66 thay vì 16.660)"})
            if not r.get("so_chung_tu") and chuan_hinh_thuc(r.get("hinh_thuc_tt", "")) == "cong_no":
                cb.append({"muc": "trung_binh", "loai": "Hoá đơn", "ngay": r["ngay"],
                           "noi_dung": f"Mua chịu không có số chứng từ ở {vi_tri} – khó đối chiếu khi trả nợ"})
            khoa_trung = (r["ngay"], chuan_hoa_ten(r["ncc"]), chuan_hoa_ten(r["ten_hang"]),
                          r["so_luong"], r["thanh_tien"])
            if khoa_trung in da_thay:
                cb.append({"muc": "trung_binh", "loai": "Hoá đơn", "ngay": r["ngay"],
                           "noi_dung": f"Nghi ghi TRÙNG: {vi_tri} giống hệt dòng {da_thay[khoa_trung]}"})
            da_thay[khoa_trung] = r["_dong"]
            chuan = (nvl or {}).get("don_gia_chuan") or gia_gan_nhat.get(khoa_gia)
            gia_tri_dong = r["thanh_tien"] if r["thanh_tien"] is not None else r["so_luong"] * dg if dg else 0
            lech = abs(dg - chuan) / chuan if chuan and dg else 0
            if (chuan and dg and dg >= 500 and lech > nguong_gia
                    and (gia_tri_dong >= dl.nguong("gia_tri_dong_canh_bao_gia") or lech > 0.5)):
                cb.append({"muc": "trung_binh" if dg > chuan else "thap", "loai": "Giá mua",
                           "ngay": r["ngay"],
                           "noi_dung": f"Giá {r['ten_hang']} ({r['ncc']}) {dinh_dang_tien(dg)}đ lệch "
                                       f"{(dg - chuan) / chuan * 100:+.0f}% so với giá chuẩn/lần trước "
                                       f"{dinh_dang_tien(chuan)}đ"})
        if dg and dg >= 500:
            gia_gan_nhat[khoa_gia] = dg

    # Khoản chi NVL ở Sổ Quỹ mang tên NCC đang có nợ -> có thể là trả nợ bị ghi thành mua mới
    no_ncc: dict[str, date] = {}
    so_no_ncc: dict[str, list[float]] = defaultdict(list)
    for r in dl["nhap_hang.csv"]:
        if chuan_hinh_thuc(r.get("hinh_thuc_tt", "")) == "cong_no":
            k = chuan_hoa_ten(r["ncc"])
            no_ncc[k] = min(no_ncc.get(k, r["ngay"]), r["ngay"])
            so_no_ncc[k].append(r["thanh_tien"] or 0)
    for r in dl["cong_no_ncc_dau_ky.csv"]:
        k = chuan_hoa_ten(r["ncc"])
        no_ncc[k] = min(no_ncc.get(k, r["ngay"]), r["ngay"])
        so_no_ncc[k].append(r["so_tien"])
    for r in trong_khoang(dl["chi_phi.csv"], tu, den):
        k = chuan_hoa_ten(r.get("noi_dung", ""))
        if r["nhom_chi_phi"] in ("nvl_bep", "nvl_bar") and k in no_ncc and no_ncc[k] < r["ngay"]:
            khop = any(abs(v - r["so_tien"]) <= 1000 for v in so_no_ncc.get(k, []))
            cb.append({"muc": "cao" if khop else "thap", "loai": "Công nợ NCC", "ngay": r["ngay"],
                       "noi_dung": f"Sổ Quỹ ghi chi NVL '{r['noi_dung']}' {dinh_dang_tien(r['so_tien'])}đ – NCC này "
                                   "đang có nợ" + (" và số tiền KHỚP ĐÚNG một khoản nợ" if khop else "") +
                                   ". Nếu đây là TRẢ NỢ thì chuyển sang thanh_toan_ncc.csv để không tính giá vốn "
                                   "hai lần"})
    return cb


def tong_hop_mua_hang(dl: DuLieu, tu: date, den: date) -> dict:
    ds = trong_khoang(dl["nhap_hang.csv"], tu, den)
    theo_ht: dict[str, float] = defaultdict(float)
    theo_ncc: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    ten_hien_thi: dict[str, str] = {}
    for r in ds:
        ht = chuan_hinh_thuc(r.get("hinh_thuc_tt", ""))
        tien = r["thanh_tien"] if r["thanh_tien"] is not None else r["so_luong"] * (r["don_gia"] or 0)
        theo_ht[ht] += tien
        ten = ten_hien_thi.setdefault(chuan_hoa_ten(r["ncc"]), r["ncc"])
        theo_ncc[ten][ht] += tien
        theo_ncc[ten]["tong"] += tien
    tra_no = trong_khoang(dl["thanh_toan_ncc.csv"], tu, den)
    return {"so_dong": len(ds), "tong": sum(theo_ht.values()), "theo_hinh_thuc": dict(theo_ht),
            "theo_ncc": {k: dict(v) for k, v in theo_ncc.items()},
            "tra_no_ncc": sum(r["so_tien"] for r in tra_no), "chi_tiet_tra_no": tra_no}


def tinh_cong_no_khach(dl: DuLieu, ngay_chot: date) -> dict:
    """Phải thu khách = tổng cột cong_no_khach (QTBH) − tổng thu nợ khách."""
    phat_sinh = sum(r["cong_no_khach"] for r in dl["doanh_thu_ngay.csv"] if r["ngay"] <= ngay_chot)
    da_thu = sum(r["so_tien"] for r in dl["thu_no_khach.csv"] if r["ngay"] <= ngay_chot)
    chi_tiet: dict[str, float] = defaultdict(float)
    for r in dl["cong_no_khach_chi_tiet.csv"]:
        if r["ngay"] <= ngay_chot:
            chi_tiet[r["khach_hang"]] += r["so_tien"]
    for r in dl["thu_no_khach.csv"]:
        if r["ngay"] <= ngay_chot:
            chi_tiet[r["khach_hang"]] -= r["so_tien"]
    return {"phat_sinh": phat_sinh, "da_thu": da_thu, "con_phai_thu": phat_sinh - da_thu,
            "theo_khach": {k: v for k, v in chi_tiet.items() if abs(v) > 0.5}}
