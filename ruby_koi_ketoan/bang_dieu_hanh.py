"""Xuất số liệu cho trang theo dõi "Ruby Koi Điều Hành" (một màn hình, ít chữ).

Tạo 5 file JSON (mảng các dòng) trong thư mục ra:
  tong_quan.json  1 dòng: các con số lớn của tháng hiện tại
  ngay.json       doanh thu từng ngày
  thang.json      mỗi tháng một dòng: doanh thu, dự báo, hoà vốn, lãi (nếu đủ Sổ Quỹ)
  cong_no.json    các khoản nợ nhà cung cấp còn treo
  viec.json       tối đa 5 việc chị cần làm, việc gấp trước
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from .bao_cao import do_day_du
from .cong_no import tinh_cong_no_khach, tinh_cong_no_ncc
from .doanh_thu import doanh_thu_ngay, kiem_soat_doanh_thu, tong_hop_doanh_thu
from .du_lieu import DuLieu
from .lai_lo import lai_lo
from .nhap_xuat_ton import tinh_nhap_xuat_ton
from .tien_ich import cac_ngay, chia, cuoi_thang, dau_thang, so_ngay_trong_thang


def _tron(x):
    return None if x is None else round(x)


def _cac_thang(dl: DuLieu, den: date) -> list[date]:
    thang = sorted({r["ngay"].replace(day=1) for r in dl["doanh_thu_ngay.csv"] if r["ngay"] <= den})
    return thang


def du_lieu_bang(dl: DuLieu, den: date) -> dict[str, list[dict]]:
    dau = dau_thang(den)

    # ---- Từng ngày
    ngay = []
    for t in _cac_thang(dl, den):
        for n in cac_ngay(t, min(cuoi_thang(t), den)):
            d = doanh_thu_ngay(dl, n)
            if d is None:
                continue
            ngay.append({
                "ngay": n.isoformat(), "thang": f"{n:%Y-%m}", "thu": d["thu"],
                "cuoi_tuan": d["thu"] in ("T6", "T7", "CN"),
                "doanh_thu": _tron(d["doanh_thu_thuan"]), "so_khach": _tron(d["so_khach"]),
                "tb_khach": _tron(d["tb_khach"]), "tien_mat": _tron(d["tien_mat"]),
                "ck_the": _tron(d["chuyen_khoan"] + d["the"]), "khach_no": _tron(d["cong_no_khach"]),
            })

    # ---- Từng tháng
    hoa_von = dl.cau_hinh.get("doanh_thu_hoa_von_thang") or 0
    thang = []
    for t in _cac_thang(dl, den):
        cuoi = min(cuoi_thang(t), den)
        dt = tong_hop_doanh_thu(dl, t, cuoi)
        du = do_day_du(dl, t, cuoi)
        du_chi_phi = not du["thieu_chi_phi"]
        pl = lai_lo(dl, tinh_nhap_xuat_ton(dl, t, cuoi), t, cuoi) if du_chi_phi else None
        thang.append({
            "thang": f"{t:%Y-%m}", "ten": f"T{t.month}", "so_ngay_co_so": dt["so_ngay_co_so"],
            "so_ngay_thang": so_ngay_trong_thang(t), "doanh_thu": _tron(dt["cong"].get("doanh_thu_thuan", 0)),
            "du_bao": _tron(dt["du_bao_thang"]), "hoa_von": _tron(hoa_von),
            "du_so_quy": du_chi_phi,
            "gia_von": _tron(pl["gia_von"]["tong"]) if pl else None,
            "food_cost": round(pl["ty_le"]["food_cost"], 4) if pl and pl["ty_le"]["food_cost"] is not None else None,
            "nhan_su": _tron(pl["tong_nhan_su"]) if pl else None,
            "van_hanh": _tron(pl["tong_van_hanh"]) if pl else None,
            "ebitda": _tron(pl["ebitda"]) if pl else None,
        })

    # ---- Tổng quan tháng hiện tại (so cùng số ngày tháng trước)
    dt = tong_hop_doanh_thu(dl, dau, den)
    so_ngay = (den - dau).days + 1
    dau_truoc = dau_thang(dau - timedelta(days=1))
    den_truoc = min(dau_truoc + timedelta(days=so_ngay - 1), cuoi_thang(dau_truoc))
    dt_truoc = tong_hop_doanh_thu(dl, dau_truoc, den_truoc)
    c, ct = dt["cong"], dt_truoc["cong"]
    cn = tinh_cong_no_ncc(dl, den)
    kh = tinh_cong_no_khach(dl, den)
    tong_quan = [{
        "den_ngay": den.isoformat(), "thang": f"{den:%Y-%m}", "ten_thang": f"Tháng {den.month}",
        "so_ngay": so_ngay, "so_ngay_thang": so_ngay_trong_thang(den),
        "doanh_thu": _tron(c.get("doanh_thu_thuan", 0)),
        "doanh_thu_ky_truoc": _tron(ct.get("doanh_thu_thuan", 0)) if dt_truoc["so_ngay_co_so"] else None,
        "tang_giam": (round(chia(c.get("doanh_thu_thuan", 0) - ct.get("doanh_thu_thuan", 0),
                                 ct.get("doanh_thu_thuan", 0)), 4)
                      if dt_truoc["so_ngay_co_so"] and ct.get("doanh_thu_thuan") else None),
        "du_bao": _tron(dt["du_bao_thang"]), "hoa_von": _tron(hoa_von),
        "dat_hoa_von_du_bao": round(chia(dt["du_bao_thang"] or 0, hoa_von), 4) if hoa_von else None,
        "tb_ngay": _tron(chia(c.get("doanh_thu_thuan", 0), dt["so_ngay_co_so"])),
        "hoa_von_ngay": _tron(hoa_von / so_ngay_trong_thang(den)) if hoa_von else None,
        "so_khach": _tron(c.get("so_khach")), "tb_khach": _tron(dt["tb_khach"]),
        "ty_le_tien_mat": round(dt["ty_trong_thanh_toan"]["Tiền mặt"] or 0, 4),
        "cong_no_ncc": _tron(cn.tong_con_no()), "khach_no": _tron(kh["con_phai_thu"]),
        "cap_nhat": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }]

    # ---- Công nợ NCC
    cong_no = [{"ncc": h.ncc, "chung_tu": h.so_chung_tu, "ngay": h.ngay.isoformat(), "han": h.han.isoformat(),
                "con_no": _tron(h.con_lai), "qua_han": max(0, (den - h.han).days)}
               for h in sorted(cn.con_no(), key=lambda h: -h.con_lai)]

    # ---- Việc cần làm (tối đa 5, gấp trước)
    viec = []
    thieu = []
    for t in _cac_thang(dl, den):
        du = do_day_du(dl, t, min(cuoi_thang(t), den))
        if du["thieu_chi_phi"]:
            thieu.append((t, len(du["thieu_chi_phi"])))
    if thieu:
        ten = ", ".join(f"T{t.month}" for t, _ in thieu)
        viec.append({"muc": "cao", "viec": f"Gửi Sổ Quỹ {ten} lên Drive",
                     "vi_sao": f"{sum(n for _, n in thieu)} ngày chưa có chi phí nên chưa tính được lãi", "so_tien": None})
    for h in sorted(cn.con_no(), key=lambda h: -(den - h.han).days):
        qua = (den - h.han).days
        if qua > 0:
            viec.append({"muc": "cao" if qua > 30 else "vua", "viec": f"Xác nhận hoặc trả nợ {h.ncc}",
                         "vi_sao": f"Quá hạn {qua} ngày (hoá đơn {h.ngay:%d/%m})", "so_tien": _tron(h.con_lai)})
    cb_dt = [c for c in kiem_soat_doanh_thu(dl, dau, den)
             if c["loai"] == "Quỹ tiền mặt" or "không cân" in c["noi_dung"]]
    if cb_dt:
        ngay_loi = ", ".join(f"{c['ngay']:%d/%m}" for c in cb_dt[:3])
        viec.append({"muc": "vua", "viec": f"Soát sổ thu ngân ngày {ngay_loi}",
                     "vi_sao": "Tiền mặt theo POS không khớp", "so_tien": None})
    if not any(r.get("tien_mat_dem") is not None for r in dl["doanh_thu_ngay.csv"] if r["ngay"] >= dau):
        viec.append({"muc": "vua", "viec": "Thu ngân ghi tiền mặt đếm cuối ngày",
                     "vi_sao": "Chưa đối chiếu được két với sổ", "so_tien": None})
    if not dl["ton_dau_ky.csv"]:
        viec.append({"muc": "vua", "viec": f"Kiểm kê {len(dl['danh_muc_nvl.csv']) or 16} nguyên liệu chính một lần",
                     "vi_sao": "Để bắt đầu đo hao hụt", "so_tien": None})
    viec = sorted(viec, key=lambda v: 0 if v["muc"] == "cao" else 1)[:5]
    for i, v in enumerate(viec, 1):
        v["stt"] = i

    return {"tong_quan": tong_quan, "ngay": ngay, "thang": thang, "cong_no": cong_no, "viec": viec}


def xuat_bang(dl: DuLieu, den: date, thu_muc: Path) -> list[Path]:
    thu_muc = Path(thu_muc)
    thu_muc.mkdir(parents=True, exist_ok=True)
    ra = []
    for ten, dong in du_lieu_bang(dl, den).items():
        tep = thu_muc / f"{ten}.json"
        tep.write_text(json.dumps(dong, ensure_ascii=False, indent=1), encoding="utf-8")
        ra.append(tep)
    return ra
