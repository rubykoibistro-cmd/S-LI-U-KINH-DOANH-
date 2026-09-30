"""Nhập – Xuất – Tồn – Hao hụt theo từng nguyên vật liệu, từng ngày.

Công thức (tính theo đơn vị của NVL, định giá bình quân gia quyền di động):

    Tồn lý thuyết cuối ngày = Tồn đầu + Nhập − Xuất bán (theo định lượng × số món POS) − Huỷ ghi nhận
    Chênh lệch kiểm kê       = Tồn thực tế (kiểm kho) − Tồn lý thuyết
                               âm  -> hao hụt KHÔNG rõ lý do (thất thoát)
                               dương -> thừa (định lượng khai cao / quên ghi nhập / món bán chưa làm)
    Tồn cuối chốt            = Tồn thực tế nếu có kiểm kho, ngược lại = Tồn lý thuyết
    Giá vốn thực tế          = Tồn đầu + Nhập − Tồn cuối chốt  (= xuất bán + huỷ + thất thoát − thừa)

Ngày nào không kiểm kho thì chênh lệch dồn sang lần kiểm kho kế tiếp, nên kiểm kê hàng tuần
vẫn ra số tháng chính xác. Hàng quan_ly_ton = khong (rau chợ mua dùng ngay) vào thẳng giá vốn
ngày mua.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from .du_lieu import DuLieu
from .tien_ich import cac_ngay, chia, dinh_dang_pct, dinh_dang_so, dinh_dang_tien


@dataclass
class DongTon:
    ngay: date
    ma_nvl: str
    ten_nvl: str
    nhom: str
    don_vi: str
    ton_dau: float = 0.0
    nhap: float = 0.0
    gia_tri_nhap: float = 0.0
    xuat_ban: float = 0.0
    huy: float = 0.0
    ton_ly_thuyet: float = 0.0
    thuc_te: float | None = None
    chenh_lech: float = 0.0
    ton_cuoi: float = 0.0
    gia_bq: float = 0.0
    gia_tri_ton_dau: float = 0.0
    co_dinh_luong: bool = True

    @property
    def that_thoat(self) -> float:
        return -self.chenh_lech if self.chenh_lech < 0 else 0.0

    @property
    def thua(self) -> float:
        return self.chenh_lech if self.chenh_lech > 0 else 0.0

    @property
    def gia_tri_xuat_ban(self) -> float:
        return self.xuat_ban * self.gia_bq

    @property
    def gia_tri_huy(self) -> float:
        return self.huy * self.gia_bq

    @property
    def gia_tri_chenh_lech(self) -> float:
        return self.chenh_lech * self.gia_bq

    @property
    def gia_tri_ton_cuoi(self) -> float:
        return self.ton_cuoi * self.gia_bq

    @property
    def gia_von_thuc_te(self) -> float:
        return self.gia_tri_ton_dau + self.gia_tri_nhap - self.gia_tri_ton_cuoi


@dataclass
class KetQuaKho:
    tu: date
    den: date
    dong: list[DongTon] = field(default_factory=list)
    # Mua dùng ngay / chưa mã hoá: ngày -> danh sách dòng nhập
    mua_dung_ngay: dict[date, list[dict]] = field(default_factory=lambda: defaultdict(list))
    chua_ma_hoa: dict[date, list[dict]] = field(default_factory=lambda: defaultdict(list))
    mon_chua_dinh_luong: dict[str, dict] = field(default_factory=dict)
    chua_co_ton_dau: list[dict] = field(default_factory=list)
    canh_bao: list[dict] = field(default_factory=list)

    def theo_ngay(self, ngay: date) -> list[DongTon]:
        return [d for d in self.dong if d.ngay == ngay]

    def gia_von_ngay(self, ngay: date) -> dict:
        """Biến động kho trong ngày. Giá trị MUA hàng lấy ở lai_lo (Sổ Quỹ + mua chịu) để không
        tính hai lần; ở đây chỉ trả phần tăng/giảm tồn kho và các chỉ số hao hụt."""
        ds = self.theo_ngay(ngay)
        xuat = sum(d.gia_von_thuc_te for d in ds)
        nhap = sum(d.gia_tri_nhap for d in ds)
        return {
            "xuat_kho_thuc_te": xuat,
            "nhap_kho": nhap,
            "giam_ton": xuat - nhap,
            "gia_von_ly_thuyet": sum(d.gia_tri_xuat_ban for d in ds),
            "huy": sum(d.gia_tri_huy for d in ds),
            "that_thoat": sum(d.that_thoat * d.gia_bq for d in ds),
            "thua": sum(d.thua * d.gia_bq for d in ds),
            "mua_dung_ngay": sum(r["thanh_tien"] for r in self.mua_dung_ngay.get(ngay, [])),
            "chua_ma_hoa": sum(r["thanh_tien"] for r in self.chua_ma_hoa.get(ngay, [])),
        }

    def gia_von_khoang(self, tu: date, den: date) -> dict:
        tong: dict[str, float] = defaultdict(float)
        for n in cac_ngay(tu, den):
            for k, v in self.gia_von_ngay(n).items():
                tong[k] += v
        return dict(tong)


def _ma_hoa_dong_nhap(dl: DuLieu, r: dict) -> dict | None:
    if r.get("ma_nvl"):
        return dl.nvl(r["ma_nvl"])
    return dl.tim_nvl_theo_ten(r.get("ten_hang", ""))


def tinh_nhap_xuat_ton(dl: DuLieu, tu: date, den: date) -> KetQuaKho:
    kq = KetQuaKho(tu=tu, den=den)
    ton_dau_ky: dict[str, dict] = {}
    for r in sorted(dl["ton_dau_ky.csv"], key=lambda x: x["ngay"]):
        if r["ngay"] <= den:
            ton_dau_ky[r["ma_nvl"]] = r  # lấy lần chốt gần nhất trước/đến kỳ báo cáo
    muon_theo_doi = [d for d in dl["danh_muc_nvl.csv"] if (d.get("quan_ly_ton") or "co").lower() != "khong"]
    # Chỉ theo dõi tồn khi đã có số kiểm kê đầu kỳ; nếu không, tồn "ảo" sẽ làm sai giá vốn.
    danh_muc = [d for d in muon_theo_doi if d["ma_nvl"] in ton_dau_ky]
    kq.chua_co_ton_dau = [d for d in muon_theo_doi if d["ma_nvl"] not in ton_dau_ky]
    ma_quan_ly = {d["ma_nvl"] for d in danh_muc}
    ma_co_dinh_luong = {ma for ct in dl.dinh_luong.values() for ma, _ in ct}

    # --- Gom phát sinh theo (ngày, mã) ---
    nhap: dict[tuple, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for r in dl["nhap_hang.csv"]:
        nvl = _ma_hoa_dong_nhap(dl, r)
        tien = r["thanh_tien"] if r["thanh_tien"] is not None else r["so_luong"] * (r["don_gia"] or 0)
        r = {**r, "thanh_tien": tien, "ma_nvl_khop": nvl["ma_nvl"] if nvl else ""}
        if nvl is None:
            kq.chua_ma_hoa[r["ngay"]].append(r)
        elif nvl["ma_nvl"] in ma_quan_ly:
            nhap[(r["ngay"], nvl["ma_nvl"])][0] += r["so_luong"]
            nhap[(r["ngay"], nvl["ma_nvl"])][1] += tien
        else:
            kq.mua_dung_ngay[r["ngay"]].append(r)

    xuat: dict[tuple, float] = defaultdict(float)
    for r in dl["ban_hang_pos.csv"]:
        cong_thuc = dl.dinh_luong.get(r["ma_mon"])
        if not cong_thuc:
            if tu <= r["ngay"] <= den:
                m = kq.mon_chua_dinh_luong.setdefault(
                    r["ma_mon"], {"ma_mon": r["ma_mon"], "ten_mon": r.get("ten_mon", ""),
                                  "so_luong": 0.0, "thanh_tien": 0.0})
                m["so_luong"] += r["so_luong"]
                m["thanh_tien"] += r["thanh_tien"] or 0.0
            continue
        for ma_nvl, luong in cong_thuc:
            xuat[(r["ngay"], ma_nvl)] += luong * r["so_luong"]

    huy: dict[tuple, float] = defaultdict(float)
    for r in dl["xuat_huy.csv"]:
        huy[(r["ngay"], r["ma_nvl"])] += r["so_luong"]

    kiem: dict[tuple, float] = {}
    for r in dl["kiem_kho.csv"]:
        kiem[(r["ngay"], r["ma_nvl"])] = r["so_luong_thuc_te"]

    moc_nho_nhat = min(
        [r["ngay"] for r in ton_dau_ky.values()] + [k[0] for k in (*nhap, *xuat, *huy, *kiem)] + [tu]
    )

    # --- Chạy từng NVL qua từng ngày ---
    for nvl in danh_muc:
        ma = nvl["ma_nvl"]
        goc = ton_dau_ky[ma]
        bat_dau = goc["ngay"]
        ton = goc["so_luong"]
        gia = goc.get("don_gia") or nvl.get("don_gia_chuan") or 0.0
        co_dl = ma in ma_co_dinh_luong
        for n in cac_ngay(bat_dau, den):
            d = DongTon(ngay=n, ma_nvl=ma, ten_nvl=nvl["ten_nvl"], nhom=nvl.get("nhom", ""),
                        don_vi=nvl.get("don_vi", ""), ton_dau=ton, gia_tri_ton_dau=ton * gia,
                        co_dinh_luong=co_dl)
            sl_nhap, tien_nhap = nhap.get((n, ma), (0.0, 0.0))
            if sl_nhap:
                sl_sau = max(ton, 0.0) + sl_nhap
                gia = (max(ton, 0.0) * gia + tien_nhap) / sl_sau if sl_sau > 0 else gia
            d.nhap, d.gia_tri_nhap, d.gia_bq = sl_nhap, tien_nhap, gia
            d.xuat_ban = xuat.get((n, ma), 0.0)
            d.huy = huy.get((n, ma), 0.0)
            d.ton_ly_thuyet = ton + sl_nhap - d.xuat_ban - d.huy
            if (n, ma) in kiem:
                d.thuc_te = kiem[(n, ma)]
                d.chenh_lech = d.thuc_te - d.ton_ly_thuyet
                if not co_dl:
                    # Chưa có định lượng: phần giảm theo kiểm kê là lượng SỬ DỤNG, không phải thất thoát
                    d.xuat_ban += -d.chenh_lech
                    d.ton_ly_thuyet = d.thuc_te
                    d.chenh_lech = 0.0
                d.ton_cuoi = d.thuc_te
            else:
                d.ton_cuoi = d.ton_ly_thuyet
            # Giá trị tồn đầu phải khớp giá trị tồn cuối hôm trước (trước khi giá BQ đổi)
            ton = d.ton_cuoi
            if tu <= n <= den:
                kq.dong.append(d)

    _kiem_tra_kho(dl, kq)
    return kq


def _kiem_tra_kho(dl: DuLieu, kq: KetQuaKho) -> None:
    cb = kq.canh_bao
    nguong_cb = dl.nguong("hao_hut_pct_canh_bao")
    nguong_nt = dl.nguong("hao_hut_pct_nghiem_trong")

    for d in kq.dong:
        if d.ton_ly_thuyet < -1e-9:
            cb.append({"muc": "cao", "loai": "Kho", "ngay": d.ngay,
                       "noi_dung": f"{d.ten_nvl}: tồn lý thuyết ÂM {dinh_dang_so(d.ton_ly_thuyet)} {d.don_vi}"
                                   " – thiếu phiếu nhập hoặc định lượng khai sai"})

    # Hao hụt theo NVL trên cả kỳ (tính trên những ngày có kiểm kho)
    for ma, tong in tong_hop_theo_nvl(kq.dong).items():
        nvl = dl.nvl(ma) or {}
        nguong = nvl.get("nguong_hao_hut_pct") or nguong_cb
        nguong = nguong / 100 if nguong > 1 else nguong
        ty_le = tong["ty_le_hao_hut"]
        if ty_le is not None and ty_le > nguong:
            muc = "cao" if ty_le > max(nguong_nt, nguong) else "trung_binh"
            cb.append({"muc": muc, "loai": "Hao hụt", "ngay": kq.den,
                       "noi_dung": f"{tong['ten_nvl']}: hao hụt {dinh_dang_pct(ty_le)} (ngưỡng {dinh_dang_pct(nguong, 0)}) – "
                                   f"huỷ {dinh_dang_so(tong['huy'])}, thất thoát {dinh_dang_so(tong['that_thoat'])} "
                                   f"{tong['don_vi']} ≈ {dinh_dang_tien(tong['gia_tri_hao_hut'])}đ"})
        if tong["thua"] > 0 and tong["gia_tri_thua"] > 50000:
            cb.append({"muc": "thap", "loai": "Kho", "ngay": kq.den,
                       "noi_dung": f"{tong['ten_nvl']}: kiểm kho THỪA {dinh_dang_so(tong['thua'])} {tong['don_vi']} – "
                                   "xem lại định lượng hoặc phiếu nhập bị ghi thiếu"})
        ton_min = nvl.get("ton_toi_thieu") or 0
        if ton_min and tong["ton_cuoi"] < ton_min:
            cb.append({"muc": "thap", "loai": "Đặt hàng", "ngay": kq.den,
                       "noi_dung": f"{tong['ten_nvl']}: tồn {dinh_dang_so(tong['ton_cuoi'])} < tối thiểu "
                                   f"{dinh_dang_so(ton_min)} {tong['don_vi']} – cần đặt hàng"})

    chua_ma = [r for n, ds in kq.chua_ma_hoa.items() if kq.tu <= n <= kq.den for r in ds]
    if chua_ma and kq.dong:
        ten = sorted({r["ten_hang"] for r in chua_ma}, key=lambda x: x.lower())
        cb.append({"muc": "thap", "loai": "Mã hoá", "ngay": kq.den,
                   "noi_dung": f"{len(chua_ma)} dòng sổ mua hàng chưa khớp danh mục NVL (chỉ ảnh hưởng theo dõi "
                               f"tồn, không ảnh hưởng giá vốn). Ví dụ: {', '.join(ten[:12])}"})
    if kq.chua_co_ton_dau:
        cb.append({"muc": "trung_binh", "loai": "Kho", "ngay": kq.den,
                   "noi_dung": f"{len(kq.chua_co_ton_dau)} NVL cần theo dõi tồn nhưng CHƯA có số kiểm kê đầu kỳ "
                               f"(ton_dau_ky.csv): {', '.join(d['ten_nvl'] for d in kq.chua_co_ton_dau[:12])}. "
                               "Kiểm kê thực tế 1 lần để bắt đầu tính tồn & hao hụt."})
    elif not kq.dong:
        cb.append({"muc": "trung_binh", "loai": "Kho", "ngay": kq.den,
                   "noi_dung": "Chưa có danh mục NVL theo dõi tồn + kiểm kê -> giá vốn đang = tiền mua NVL, "
                               "CHƯA tách được hao hụt. Bắt đầu với 15–20 NVL giá trị cao (bò, cá, tôm, bia, rượu...)"})
    khong_dl = sorted({d.ten_nvl for d in kq.dong if not d.co_dinh_luong})
    if khong_dl:
        cb.append({"muc": "thap", "loai": "Định lượng", "ngay": kq.den,
                   "noi_dung": f"{len(khong_dl)} NVL chưa gắn vào định lượng món nào – lượng dùng đang tính theo "
                               f"kiểm kê, chưa tách được thất thoát: {', '.join(khong_dl[:12])}"})
    if kq.mon_chua_dinh_luong:
        tien = sum(m["thanh_tien"] for m in kq.mon_chua_dinh_luong.values())
        ten = ", ".join(f"{m['ten_mon'] or m['ma_mon']}" for m in
                        sorted(kq.mon_chua_dinh_luong.values(), key=lambda m: -m["thanh_tien"])[:8])
        cb.append({"muc": "trung_binh", "loai": "Định lượng", "ngay": kq.den,
                   "noi_dung": f"{len(kq.mon_chua_dinh_luong)} món bán chưa có định lượng "
                               f"(doanh thu {dinh_dang_tien(tien)}đ) – kho không trừ được: {ten}"})


def tong_hop_theo_nvl(dong: list[DongTon]) -> dict[str, dict]:
    """Gộp nhiều ngày thành một dòng/NVL (dùng cho báo cáo tháng)."""
    nhom_dong: dict[str, list[DongTon]] = defaultdict(list)
    for d in sorted(dong, key=lambda x: x.ngay):
        nhom_dong[d.ma_nvl].append(d)
    kq = {}
    for ma, ds in nhom_dong.items():
        dau, cuoi = ds[0], ds[-1]
        t = {
            "ma_nvl": ma, "ten_nvl": dau.ten_nvl, "nhom": dau.nhom, "don_vi": dau.don_vi,
            "ton_dau": dau.ton_dau, "gia_tri_ton_dau": dau.gia_tri_ton_dau,
            "nhap": sum(d.nhap for d in ds), "gia_tri_nhap": sum(d.gia_tri_nhap for d in ds),
            "xuat_ban": sum(d.xuat_ban for d in ds), "gia_tri_xuat_ban": sum(d.gia_tri_xuat_ban for d in ds),
            "huy": sum(d.huy for d in ds), "gia_tri_huy": sum(d.gia_tri_huy for d in ds),
            "that_thoat": sum(d.that_thoat for d in ds),
            "gia_tri_that_thoat": sum(d.that_thoat * d.gia_bq for d in ds),
            "thua": sum(d.thua for d in ds), "gia_tri_thua": sum(d.thua * d.gia_bq for d in ds),
            "ton_cuoi": cuoi.ton_cuoi, "gia_tri_ton_cuoi": cuoi.gia_tri_ton_cuoi, "gia_bq": cuoi.gia_bq,
            "so_lan_kiem": sum(1 for d in ds if d.thuc_te is not None),
            "gia_von_thuc_te": sum(d.gia_von_thuc_te for d in ds),
        }
        t["gia_tri_hao_hut"] = t["gia_tri_huy"] + t["gia_tri_that_thoat"]
        su_dung = t["gia_tri_xuat_ban"] + t["gia_tri_hao_hut"]
        co_dl = all(d.co_dinh_luong for d in ds)
        t["co_dinh_luong"] = co_dl
        t["ty_le_hao_hut"] = (chia(t["gia_tri_hao_hut"], su_dung)
                              if (co_dl and t["so_lan_kiem"]) or t["huy"] else None)
        kq[ma] = t
    return kq


def tong_hop_theo_nhom(dong: list[DongTon]) -> dict[str, dict]:
    kq: dict[str, dict] = {}
    for t in tong_hop_theo_nvl(dong).values():
        g = kq.setdefault(t["nhom"] or "Khác", defaultdict(float))
        for k, v in t.items():
            if k.startswith("gia_tri_") or k == "gia_von_thuc_te":
                g[k] += v
    for g in kq.values():
        g["ty_le_hao_hut"] = chia(g["gia_tri_hao_hut"], g["gia_tri_xuat_ban"] + g["gia_tri_hao_hut"])
    return kq
