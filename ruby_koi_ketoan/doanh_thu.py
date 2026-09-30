"""Doanh thu từ POS/QTBH, đối soát tiền mặt thu ngân và phân tích doanh thu."""
from __future__ import annotations

from collections import defaultdict
from datetime import date

from .cong_no import chuan_hinh_thuc
from .du_lieu import DuLieu, trong_khoang
from .tien_ich import THU, cac_ngay, chia, dinh_dang_pct, dinh_dang_tien, so_ngay_trong_thang, thu_trong_tuan


def _chi_tien_mat(dl: DuLieu, ngay: date) -> dict:
    chi_phi = sum(r["so_tien"] for r in dl["chi_phi.csv"]
                  if r["ngay"] == ngay and chuan_hinh_thuc(r.get("hinh_thuc_tt", "")) == "tien_mat")
    mua = 0.0
    if dl.cau_hinh.get("nguon_mua_nvl", "so_quy") == "nhap_hang":  # chế độ so_quy: đã nằm trong chi_phi
        mua = sum((r["thanh_tien"] if r["thanh_tien"] is not None else r["so_luong"] * (r["don_gia"] or 0))
                  for r in dl["nhap_hang.csv"]
                  if r["ngay"] == ngay and chuan_hinh_thuc(r.get("hinh_thuc_tt", "")) == "tien_mat")
    tra_no = sum(r["so_tien"] for r in dl["thanh_toan_ncc.csv"]
                 if r["ngay"] == ngay and chuan_hinh_thuc(r.get("hinh_thuc_tt", "")) == "tien_mat")
    thu_no = sum(r["so_tien"] for r in dl["thu_no_khach.csv"]
                 if r["ngay"] == ngay and chuan_hinh_thuc(r.get("hinh_thuc_tt", "")) == "tien_mat")
    return {"chi_phi": chi_phi, "mua_hang": mua, "tra_no_ncc": tra_no, "thu_no_khach": thu_no,
            "tong_chi": chi_phi + mua + tra_no}


def doanh_thu_ngay(dl: DuLieu, ngay: date) -> dict | None:
    ds = [r for r in dl["doanh_thu_ngay.csv"] if r["ngay"] == ngay]
    if not ds:
        return None
    g = lambda k: sum((r.get(k) or 0.0) for r in ds)  # noqa: E731 – một ngày có thể nhiều ca
    co = lambda k: any(r.get(k) is not None for r in ds)  # noqa: E731
    kq = {
        "ngay": ngay, "thu": thu_trong_tuan(ngay),
        "doanh_thu_gop": g("doanh_thu_gop"), "giam_gia": g("giam_gia"),
        "tiep_khach_noi_bo": g("tiep_khach_noi_bo"), "tru_lui": g("tru_lui"),
        "cong_no_khach": g("cong_no_khach"), "chuyen_khoan": g("chuyen_khoan"), "the": g("the"),
        "so_khach": g("so_khach") if co("so_khach") else None,
        "so_hoa_don": g("so_hoa_don") if co("so_hoa_don") else None,
        "ghi_chu": "; ".join(r.get("ghi_chu", "") for r in ds if r.get("ghi_chu")),
    }
    kq["giam_tru"] = kq["giam_gia"] + kq["tiep_khach_noi_bo"] + kq["tru_lui"]
    kq["doanh_thu_thuan"] = kq["doanh_thu_gop"] - kq["giam_tru"]
    kq["thuc_thu"] = kq["doanh_thu_thuan"] - kq["cong_no_khach"]
    kq["tien_mat_tinh"] = kq["thuc_thu"] - kq["chuyen_khoan"] - kq["the"]
    kq["tien_mat_pos"] = g("tien_mat") if co("tien_mat") else None
    kq["tien_mat"] = kq["tien_mat_pos"] if kq["tien_mat_pos"] is not None else kq["tien_mat_tinh"]
    kq["tb_khach"] = chia(kq["doanh_thu_thuan"], kq["so_khach"]) if kq["so_khach"] else None

    chi = _chi_tien_mat(dl, ngay)
    kq["chi_tien_mat"] = chi
    kq["tien_mat_phai_con"] = kq["tien_mat"] + chi["thu_no_khach"] - chi["tong_chi"]
    kq["tien_mat_dem"] = g("tien_mat_dem") if co("tien_mat_dem") else None
    kq["chenh_lech_quy"] = (kq["tien_mat_dem"] - kq["tien_mat_phai_con"]
                            if kq["tien_mat_dem"] is not None else None)

    pos = [r for r in dl["ban_hang_pos.csv"] if r["ngay"] == ngay]
    kq["pos_tong_mon"] = sum((r["thanh_tien"] if r["thanh_tien"] is not None
                              else r["so_luong"] * (r["don_gia"] or 0)) for r in pos) if pos else None
    return kq


def kiem_soat_doanh_thu(dl: DuLieu, tu: date, den: date) -> list[dict]:
    cb = []
    nguong_quy = dl.nguong("lech_quy_tien_mat")
    nguong_pos = dl.nguong("lech_pos_vs_qtbh_pct")
    for n in cac_ngay(tu, den):
        d = doanh_thu_ngay(dl, n)
        if d is None:
            cb.append({"muc": "cao", "loai": "Doanh thu", "ngay": n,
                       "noi_dung": f"Chưa có số QTBH/POS ngày {n:%d/%m} – báo cáo ngày này chưa đầy đủ"})
            continue
        if d["tien_mat_pos"] is not None and abs(d["tien_mat_pos"] - d["tien_mat_tinh"]) > 1000:
            cb.append({"muc": "cao", "loai": "Doanh thu", "ngay": n,
                       "noi_dung": f"QTBH không cân: tiền mặt POS {dinh_dang_tien(d['tien_mat_pos'])} ≠ "
                                   f"thực thu − CK − thẻ = {dinh_dang_tien(d['tien_mat_tinh'])} "
                                   f"(lệch {dinh_dang_tien(d['tien_mat_pos'] - d['tien_mat_tinh'])})"})
        if d["chenh_lech_quy"] is not None and abs(d["chenh_lech_quy"]) > nguong_quy:
            loai = "THIẾU" if d["chenh_lech_quy"] < 0 else "THỪA"
            cb.append({"muc": "cao", "loai": "Quỹ tiền mặt", "ngay": n,
                       "noi_dung": f"{loai} quỹ {dinh_dang_tien(abs(d['chenh_lech_quy']))}đ: đếm "
                                   f"{dinh_dang_tien(d['tien_mat_dem'])} vs sổ phải còn "
                                   f"{dinh_dang_tien(d['tien_mat_phai_con'])} (đã trừ chi tiền mặt "
                                   f"{dinh_dang_tien(d['chi_tien_mat']['tong_chi'])})"})
        if "≠TỔNG" in d["ghi_chu"]:
            cb.append({"muc": "trung_binh", "loai": "Doanh thu", "ngay": n,
                       "noi_dung": f"DSR/QTBH: {d['ghi_chu']} – tách CK theo ca bị sai, cần soát lại ô CA1/CA2/CK "
                                   "(báo cáo đang lấy ô TỔNG CỘNG vì khớp tiền phải nộp)"})
        if d["pos_tong_mon"] is not None and d["doanh_thu_gop"]:
            lech = d["pos_tong_mon"] - d["doanh_thu_gop"]
            if abs(lech) / d["doanh_thu_gop"] > nguong_pos:
                cb.append({"muc": "trung_binh", "loai": "Doanh thu", "ngay": n,
                           "noi_dung": f"Tổng bán theo món POS {dinh_dang_tien(d['pos_tong_mon'])} lệch QTBH "
                                       f"{dinh_dang_tien(d['doanh_thu_gop'])} ({dinh_dang_tien(lech)}) – "
                                       "kiểm tra món huỷ/đổi, phụ thu"})
        if d["doanh_thu_gop"] and d["giam_tru"] / d["doanh_thu_gop"] > 0.05:
            cb.append({"muc": "trung_binh", "loai": "Doanh thu", "ngay": n,
                       "noi_dung": f"Giảm trừ cao {dinh_dang_pct(d['giam_tru'] / d['doanh_thu_gop'])} doanh thu "
                                   f"(giảm giá {dinh_dang_tien(d['giam_gia'])}, tiếp khách/nội bộ "
                                   f"{dinh_dang_tien(d['tiep_khach_noi_bo'])}, trừ lui {dinh_dang_tien(d['tru_lui'])})"})
    return cb


def tong_hop_doanh_thu(dl: DuLieu, tu: date, den: date) -> dict:
    ngay = [d for n in cac_ngay(tu, den) if (d := doanh_thu_ngay(dl, n))]
    cong = defaultdict(float)
    for d in ngay:
        for k in ("doanh_thu_gop", "giam_gia", "tiep_khach_noi_bo", "tru_lui", "giam_tru",
                  "doanh_thu_thuan", "cong_no_khach", "thuc_thu", "chuyen_khoan", "the", "tien_mat"):
            cong[k] += d[k]
        if d["so_khach"]:
            cong["so_khach"] += d["so_khach"]
        if d["chenh_lech_quy"] is not None:
            cong["chenh_lech_quy"] += d["chenh_lech_quy"]
    theo_thu = {t: {"so_ngay": 0, "doanh_thu_thuan": 0.0} for t in THU}
    for d in ngay:
        theo_thu[d["thu"]]["so_ngay"] += 1
        theo_thu[d["thu"]]["doanh_thu_thuan"] += d["doanh_thu_thuan"]
    for t in theo_thu.values():
        t["binh_quan"] = chia(t["doanh_thu_thuan"], t["so_ngay"])
        t["ty_trong"] = chia(t["doanh_thu_thuan"], cong["doanh_thu_thuan"])

    so_ngay_thang = so_ngay_trong_thang(den)
    so_ngay_co_so = len(ngay)
    du_bao = chia(cong["doanh_thu_thuan"], so_ngay_co_so)
    du_bao = du_bao * so_ngay_thang if du_bao is not None else None
    muc_tieu = dl.cau_hinh.get("muc_tieu_doanh_thu_thang") or 0
    hoa_von = dl.cau_hinh.get("doanh_thu_hoa_von_thang") or 0
    return {
        "ngay": ngay, "cong": dict(cong), "so_ngay_co_so": so_ngay_co_so, "theo_thu": theo_thu,
        "tb_khach": chia(cong["doanh_thu_thuan"], cong.get("so_khach", 0)),
        "du_bao_thang": du_bao, "muc_tieu": muc_tieu, "hoa_von": hoa_von,
        "dat_muc_tieu": chia(cong["doanh_thu_thuan"], muc_tieu) if muc_tieu else None,
        "dat_hoa_von": chia(cong["doanh_thu_thuan"], hoa_von) if hoa_von else None,
        "ty_trong_thanh_toan": {
            "Tiền mặt": chia(cong["tien_mat"], cong["thuc_thu"]),
            "Chuyển khoản": chia(cong["chuyen_khoan"], cong["thuc_thu"]),
            "Thẻ": chia(cong["the"], cong["thuc_thu"]),
        },
    }


def top_mon(dl: DuLieu, tu: date, den: date, so: int = 10) -> list[dict]:
    gom: dict[str, dict] = {}
    for r in trong_khoang(dl["ban_hang_pos.csv"], tu, den):
        m = gom.setdefault(r["ma_mon"], {"ma_mon": r["ma_mon"], "ten_mon": r.get("ten_mon", ""),
                                         "so_luong": 0.0, "thanh_tien": 0.0})
        m["so_luong"] += r["so_luong"]
        m["thanh_tien"] += r["thanh_tien"] if r["thanh_tien"] is not None else r["so_luong"] * (r["don_gia"] or 0)
    return sorted(gom.values(), key=lambda m: -m["thanh_tien"])[:so]
