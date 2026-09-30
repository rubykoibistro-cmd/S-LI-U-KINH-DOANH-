"""Dòng lệnh: python -m ruby_koi_ketoan <lệnh> ...  (chạy `-h` để xem hướng dẫn)."""
from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

from . import nhap_file
from .bao_cao import MUC, lap_bao_cao, tinh_toan
from .du_lieu import mo_ta_bang, nap_du_lieu, tao_mau
from .tien_ich import cuoi_thang, doc_ngay, doc_thang


def _ngay(s: str) -> date:
    d = doc_ngay(s)
    if d is None:
        raise argparse.ArgumentTypeError(f"Ngày không hợp lệ: {s} (dùng 2026-09-29 hoặc 29/09/2026)")
    return d


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="ruby_koi_ketoan", description="Kế toán nội bộ Ruby Koi Bistro")
    ap.add_argument("--du-lieu", default="du_lieu", help="thư mục dữ liệu (mặc định: du_lieu)")
    ap.add_argument("--ra", default="bao_cao", help="thư mục xuất báo cáo (mặc định: bao_cao)")
    sub = ap.add_subparsers(dest="lenh", required=True)

    sub.add_parser("tao-mau", help="tạo các file CSV trống + cau_hinh.json + MO_TA_DU_LIEU.md")

    p = sub.add_parser("nhap-dsr", help="nhập QTBH/SALES/PM/sổ chi từ file DSR tháng (.xlsx)")
    p.add_argument("tep")
    p.add_argument("--den-ngay", type=_ngay, help="chỉ nhập đến ngày này (bỏ các ngày chưa chốt)")

    p = sub.add_parser("nhap-so-quy", help="nhập chi phí từ Sổ Quỹ tháng (.xlsx, 31 sheet ngày)")
    p.add_argument("tep")
    p.add_argument("--thang", required=True, help="tháng của sổ, vd 2026-08")

    p = sub.add_parser("nhap-so-mua-hang", help="nhập sổ mua hàng chi tiết (.xlsx)")
    p.add_argument("tep")

    p = sub.add_parser("nhap-ipos", help="nhập báo cáo bán theo mặt hàng từ iPOS cho 1 ngày")
    p.add_argument("tep")
    p.add_argument("--ngay", type=_ngay, required=True)

    p = sub.add_parser("bao-cao-ngay", help="lập báo cáo ngày (mặc định: hôm qua)")
    p.add_argument("--ngay", type=_ngay, default=date.today() - timedelta(days=1))
    p.add_argument("--in", dest="in_ra", action="store_true", help="in báo cáo ra màn hình")

    p = sub.add_parser("bao-cao-thang", help="lập báo cáo tháng")
    p.add_argument("--thang", required=True, help="vd 2026-09")
    p.add_argument("--den-ngay", type=_ngay, help="chốt đến ngày (mặc định cuối tháng)")
    p.add_argument("--in", dest="in_ra", action="store_true")

    p = sub.add_parser("kiem-tra", help="chỉ soát lỗi số liệu, in danh sách cảnh báo")
    p.add_argument("--tu", type=_ngay)
    p.add_argument("--den", type=_ngay, default=date.today() - timedelta(days=1))

    a = ap.parse_args(argv)
    du_lieu, ra = Path(a.du_lieu), Path(a.ra)

    if a.lenh == "tao-mau":
        for tep in tao_mau(du_lieu):
            print("  tạo", tep)
        (du_lieu / "MO_TA_DU_LIEU.md").write_text(mo_ta_bang(), encoding="utf-8")
        print("  tạo", du_lieu / "MO_TA_DU_LIEU.md")
        return 0
    if a.lenh.startswith("nhap-"):
        tao_mau(du_lieu)
        if a.lenh == "nhap-dsr":
            dong = nhap_file.nhap_dsr(Path(a.tep), du_lieu, a.den_ngay)
        elif a.lenh == "nhap-so-quy":
            dong = nhap_file.nhap_so_quy(Path(a.tep), du_lieu, doc_thang(a.thang))
        elif a.lenh == "nhap-so-mua-hang":
            dong = nhap_file.nhap_so_mua_hang(Path(a.tep), du_lieu)
        else:
            dong = nhap_file.nhap_ipos_mat_hang(Path(a.tep), du_lieu, a.ngay)
        print("\n".join(dong))
        return 0

    dl = nap_du_lieu(du_lieu)
    if a.lenh == "bao-cao-ngay":
        kq = lap_bao_cao(dl, a.ngay, a.ngay, "ngay", ra)
    elif a.lenh == "bao-cao-thang":
        dau = doc_thang(a.thang)
        kq = lap_bao_cao(dl, dau, a.den_ngay or cuoi_thang(dau), "thang", ra)
    else:
        tu = a.tu or a.den.replace(day=1)
        cb = tinh_toan(dl, tu, a.den)["canh_bao"]
        for c in cb:
            print(f"{MUC.get(c['muc'], '')} [{c['loai']}] {c['ngay']:%d/%m} – {c['noi_dung']}")
        print(f"\nTổng: {len(cb)} cảnh báo ({sum(1 for c in cb if c['muc'] == 'cao')} mức cao)")
        return 1 if any(c["muc"] == "cao" for c in cb) else 0
    if a.in_ra:
        print(kq["markdown"])
    print(f"Đã lưu: {kq['tep_md']}\n        {kq['tep_xlsx']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
