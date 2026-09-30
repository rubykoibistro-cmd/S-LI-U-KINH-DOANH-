"""Kết quả kinh doanh (P&L) theo ngày / tháng và dòng tiền."""
from __future__ import annotations

from collections import defaultdict
from datetime import date

from .cong_no import chuan_hinh_thuc
from .doanh_thu import tong_hop_doanh_thu
from .du_lieu import NHOM_CHI_PHI, NHOM_GIA_VON, NHOM_TAI_CHINH, DuLieu, trong_khoang
from .nhap_xuat_ton import KetQuaKho
from .tien_ich import cac_ngay, chia, cuoi_thang, doc_thang, so_ngay_trong_thang

NHOM_NHAN_SU = {"luong", "thoi_vu", "bhxh"}


def ngay_hieu_luc(r: dict) -> date:
    """Khoản chi thuộc kỳ nào: nếu ky_phan_bo khác tháng chi -> ghi nhận vào cuối tháng ky_phan_bo."""
    ky = (r.get("ky_phan_bo") or "").strip()
    if not ky:
        return r["ngay"]
    try:
        thang = doc_thang(ky)
    except ValueError:
        return r["ngay"]
    if (thang.year, thang.month) == (r["ngay"].year, r["ngay"].month):
        return r["ngay"]
    return cuoi_thang(thang)


def phan_bo_co_dinh(dl: DuLieu, tu: date, den: date) -> dict[str, float]:
    """Chi phí cố định tháng (mặt bằng, BHXH...) + khấu hao phân bổ đều theo số ngày."""
    kq: dict[str, float] = defaultdict(float)
    for n in cac_ngay(tu, den):
        so_ngay = so_ngay_trong_thang(n)
        for nhom, cfg in dl.cau_hinh.get("chi_phi_co_dinh_thang", {}).items():
            tien = cfg["so_tien"] if isinstance(cfg, dict) else cfg
            kq[nhom] += tien / so_ngay
        kq["khau_hao"] += (dl.cau_hinh.get("khau_hao_thang") or 0) / so_ngay
    return dict(kq)


def lai_lo(dl: DuLieu, kho: KetQuaKho, tu: date, den: date) -> dict:
    dt = tong_hop_doanh_thu(dl, tu, den)
    c = dt["cong"]
    gv = kho.gia_von_khoang(tu, den)

    nhom_co_dinh = set(dl.cau_hinh.get("chi_phi_co_dinh_thang", {}))
    chi_phi: dict[str, float] = defaultdict(float)
    chi_thuc_te_co_dinh: dict[str, float] = defaultdict(float)
    loai_khoi_ky: list[dict] = []
    for r in dl["chi_phi.csv"]:
        nhl = ngay_hieu_luc(r)
        if tu <= r["ngay"] <= den and not (tu <= nhl <= den):
            loai_khoi_ky.append(r)
        if not (tu <= nhl <= den):
            continue
        nhom = r["nhom_chi_phi"] if r["nhom_chi_phi"] in NHOM_CHI_PHI else "khac"
        if nhom in nhom_co_dinh:
            chi_thuc_te_co_dinh[nhom] += r["so_tien"]
            continue
        chi_phi[nhom] += r["so_tien"]

    co_dinh = phan_bo_co_dinh(dl, tu, den)
    khau_hao = co_dinh.pop("khau_hao", 0.0)

    # Giá vốn = Mua NVL trong kỳ + (Tồn đầu − Tồn cuối) của NVL theo dõi tồn.
    mua_so_quy = sum(chi_phi.pop(n, 0.0) for n in NHOM_GIA_VON)
    nhap_ky = trong_khoang(dl["nhap_hang.csv"], tu, den)
    tien = lambda r: r["thanh_tien"] if r["thanh_tien"] is not None else r["so_luong"] * (r["don_gia"] or 0)  # noqa: E731
    mua_chiu = sum(tien(r) for r in nhap_ky if chuan_hinh_thuc(r.get("hinh_thuc_tt", "")) == "cong_no")
    if dl.cau_hinh.get("nguon_mua_nvl", "so_quy") == "nhap_hang":
        mua_nhap_hang = sum(tien(r) for r in nhap_ky)  # sổ nhập hàng chỉ chứa NVL
    else:
        mua_nhap_hang = mua_chiu  # hàng trả ngay đã nằm trong Sổ Quỹ
    tong_mua = mua_so_quy + mua_nhap_hang
    tong_gia_von = tong_mua + gv.get("giam_ton", 0.0)
    nhan_su = {k: chi_phi.pop(k) for k in list(chi_phi) if k in NHOM_NHAN_SU}
    tai_chinh = {k: chi_phi.pop(k) for k in list(chi_phi) if k in NHOM_TAI_CHINH}
    van_hanh = dict(chi_phi)
    for nhom, tien in co_dinh.items():
        if nhom in NHOM_NHAN_SU:
            nhan_su[nhom] = nhan_su.get(nhom, 0.0) + tien
        else:
            van_hanh[nhom] = van_hanh.get(nhom, 0.0) + tien

    dtt = c.get("doanh_thu_thuan", 0.0)
    ln_gop = dtt - tong_gia_von
    tong_ns = sum(nhan_su.values())
    tong_vh = sum(van_hanh.values())
    ebitda = ln_gop - tong_ns - tong_vh
    lai_vay = sum(tai_chinh.values())
    ln = ebitda - khau_hao - lai_vay
    return {
        "tu": tu, "den": den, "doanh_thu": dt,
        "doanh_thu_gop": c.get("doanh_thu_gop", 0.0), "giam_tru": c.get("giam_tru", 0.0),
        "doanh_thu_thuan": dtt,
        "gia_von": {**gv, "mua_so_quy": mua_so_quy, "mua_nhap_hang": mua_nhap_hang, "mua_chiu": mua_chiu,
                    "tong_mua": tong_mua, "tong": tong_gia_von},
        "loi_nhuan_gop": ln_gop, "nhan_su": nhan_su, "tong_nhan_su": tong_ns,
        "van_hanh": van_hanh, "tong_van_hanh": tong_vh, "ebitda": ebitda,
        "khau_hao": khau_hao, "lai_vay": lai_vay, "loi_nhuan": ln,
        "chi_thuc_te_co_dinh": dict(chi_thuc_te_co_dinh), "chi_loai_khoi_ky": loai_khoi_ky,
        "ty_le": {
            "food_cost": chia(tong_gia_von, dtt),
            "hao_hut_tren_dt": chia(gv.get("huy", 0.0) + gv.get("that_thoat", 0.0), dtt),
            "nhan_su": chia(tong_ns, dtt),
            "prime_cost": chia(tong_gia_von + tong_ns, dtt),
            "van_hanh": chia(tong_vh, dtt),
            "ebitda": chia(ebitda, dtt),
            "loi_nhuan": chia(ln, dtt),
        },
    }


def dong_tien(dl: DuLieu, tu: date, den: date) -> dict:
    """Tiền thật vào – ra trong kỳ (cơ sở tiền mặt, mọi hình thức trừ công nợ)."""
    dt = tong_hop_doanh_thu(dl, tu, den)["cong"]
    thu_no = sum(r["so_tien"] for r in trong_khoang(dl["thu_no_khach.csv"], tu, den))
    chi_phi = defaultdict(float)
    for r in trong_khoang(dl["chi_phi.csv"], tu, den):
        if chuan_hinh_thuc(r.get("hinh_thuc_tt", "")) != "cong_no":
            chi_phi[r["nhom_chi_phi"]] += r["so_tien"]
    mua_tra_ngay = 0.0
    if dl.cau_hinh.get("nguon_mua_nvl", "so_quy") == "nhap_hang":  # chế độ so_quy: đã nằm trong chi_phi
        mua_tra_ngay = sum(
            (r["thanh_tien"] if r["thanh_tien"] is not None else r["so_luong"] * (r["don_gia"] or 0))
            for r in trong_khoang(dl["nhap_hang.csv"], tu, den)
            if chuan_hinh_thuc(r.get("hinh_thuc_tt", "")) != "cong_no")
    tra_no = sum(r["so_tien"] for r in trong_khoang(dl["thanh_toan_ncc.csv"], tu, den))
    thu = dt.get("thuc_thu", 0.0) + thu_no
    chi = sum(chi_phi.values()) + mua_tra_ngay + tra_no
    return {"thu_ban_hang": dt.get("thuc_thu", 0.0), "thu_no_khach": thu_no, "tong_thu": thu,
            "chi_phi": dict(chi_phi), "mua_hang_tra_ngay": mua_tra_ngay, "tra_no_ncc": tra_no,
            "tong_chi": chi, "dong_tien_thuan": thu - chi,
            "tra_ngan_hang_thang": dl.cau_hinh.get("tra_ngan_hang_thang") or 0}
