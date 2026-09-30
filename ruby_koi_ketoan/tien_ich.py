"""Tiện ích chung: đọc số kiểu Việt Nam, đọc ngày, định dạng tiền, chuẩn hoá tên hàng."""
from __future__ import annotations

import calendar
import re
import unicodedata
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

_KHONG = {"", "-", "–", "—", "none", "nan", "null"}


def doc_so(gia_tri, mac_dinh: float = 0.0, so_luong: bool = False) -> float:
    """Đọc số từ mọi kiểu ghi thường gặp trong sổ sách Ruby Koi.

    Hỗ trợ: 1.234.567 | 1,234,567 | 1 234 567 | 0,5 | 0.5 | (1.000) | " - " | 11,825,000 đ
    Quy tắc phân biệt dấu thập phân:
      - Có cả '.' và ',' -> dấu xuất hiện sau cùng là dấu thập phân.
      - Chỉ có một loại dấu, lặp lại nhiều lần -> dấu phân cách hàng nghìn.
      - Chỉ có một dấu, theo sau đúng 3 chữ số -> hàng nghìn (1.500 = 1500).
      - Còn lại -> thập phân (0,5 = 0.5; 16,66 = 16.66).
    so_luong=True (cột số lượng/kg): một dấu duy nhất luôn là thập phân (2.002 kg = 2,002 kg).
    """
    if gia_tri is None:
        return mac_dinh
    if isinstance(gia_tri, bool):
        return float(gia_tri)
    if isinstance(gia_tri, (int, float)):
        return float(gia_tri)
    if isinstance(gia_tri, Decimal):
        return float(gia_tri)
    s = str(gia_tri).strip().lower()
    if s in _KHONG:
        return mac_dinh
    am = False
    if s.startswith("(") and s.endswith(")"):
        am, s = True, s[1:-1]
    s = re.sub(r"[^\d.,\-]", "", s)
    if s.startswith("-"):
        am, s = not am if s.count("-") == 1 else am, s.lstrip("-")
    if s in _KHONG or not re.search(r"\d", s):
        return mac_dinh
    co_cham, co_phay = "." in s, "," in s
    if co_cham and co_phay:
        thap_phan = "." if s.rfind(".") > s.rfind(",") else ","
        nghin = "," if thap_phan == "." else "."
        s = s.replace(nghin, "").replace(thap_phan, ".")
    elif co_cham or co_phay:
        dau = "." if co_cham else ","
        phan = s.split(dau)
        if len(phan) > 2 or (not so_luong and len(phan[-1]) == 3 and phan[0] not in ("", "0")):
            s = s.replace(dau, "")
        else:
            s = s.replace(dau, ".")
    try:
        so = float(Decimal(s))
    except InvalidOperation:
        return mac_dinh
    return -so if am else so


_DINH_DANG_NGAY = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%Y/%m/%d")


def doc_ngay(gia_tri) -> date | None:
    """Đọc ngày: 2026-09-29, 29/09/2026, 29.9.2026, datetime, số serial Excel."""
    if gia_tri is None:
        return None
    if isinstance(gia_tri, datetime):
        return gia_tri.date()
    if isinstance(gia_tri, date):
        return gia_tri
    if isinstance(gia_tri, (int, float)) and 20000 < gia_tri < 80000:
        return date(1899, 12, 30) + timedelta(days=int(gia_tri))
    s = str(gia_tri).strip()
    if not s:
        return None
    s = s.split(" ")[0]
    for f in _DINH_DANG_NGAY:
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            continue
    return None


def dinh_dang_tien(so: float, don_vi: str = "") -> str:
    """12345678.4 -> '12.345.678' (kiểu Việt Nam, làm tròn đồng)."""
    if so is None:
        return "-"
    n = round(so)
    chuoi = f"{abs(n):,}".replace(",", ".")
    chuoi = f"({chuoi})" if n < 0 else chuoi
    return f"{chuoi}{don_vi}"


def dinh_dang_so(so: float, le: int = 2) -> str:
    if so is None:
        return "-"
    if abs(so - round(so)) < 1e-9:
        return dinh_dang_tien(so)
    chuoi = f"{so:,.{le}f}".rstrip("0").rstrip(".")
    return chuoi.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def dinh_dang_pct(ty_le: float | None, le: int = 1) -> str:
    if ty_le is None:
        return "-"
    return f"{ty_le * 100:.{le}f}%".replace(".", ",")


def chia(tu: float, mau: float) -> float | None:
    return tu / mau if mau else None


def bo_dau(chuoi: str) -> str:
    chuoi = chuoi.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", chuoi) if unicodedata.category(c) != "Mn")


def chuan_hoa_ten(chuoi: str) -> str:
    """'  Mỳ Quảng ' -> 'my quang' để so khớp tên hàng ghi tay."""
    s = bo_dau(str(chuoi or "")).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def cac_ngay(tu: date, den: date):
    d = tu
    while d <= den:
        yield d
        d += timedelta(days=1)


def dau_thang(d: date) -> date:
    return d.replace(day=1)


def cuoi_thang(d: date) -> date:
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


def so_ngay_trong_thang(d: date) -> int:
    return calendar.monthrange(d.year, d.month)[1]


THU = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]


def thu_trong_tuan(d: date) -> str:
    return THU[d.weekday()]


def doc_thang(chuoi: str) -> date:
    """'2026-09' | '09/2026' | '9.2026' -> ngày đầu tháng."""
    s = chuoi.strip()
    m = re.fullmatch(r"(\d{4})[-/.](\d{1,2})", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), 1)
    m = re.fullmatch(r"(\d{1,2})[-/.](\d{4})", s)
    if m:
        return date(int(m.group(2)), int(m.group(1)), 1)
    raise ValueError(f"Không đọc được tháng: {chuoi!r} (dùng dạng 2026-09)")
