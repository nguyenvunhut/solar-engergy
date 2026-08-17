"""Ham dung chung cho dashboard: nap runtime C++, nap CSS va dung header bao cao."""
import ctypes
import glob
import re
from pathlib import Path

import streamlit as st

_GOC = Path(__file__).parent
_CSS_PATH = _GOC / "style.css"
_LOGO_PATH = _GOC / "assets" / "logo_fpoly.png"


def _phien_ban(duong: str) -> tuple:
    """Rut so hieu GCC tu duong dan nix store de sap xep.

    '/nix/store/xxx-gcc-15.3.0-lib/lib/libstdc++.so.6' -> (15, 3, 0)
    Khong doc duoc thi tra ve (0,) de bi xep sau cung.
    """
    m = re.search(r"gcc-(\d+)\.(\d+)\.(\d+)", duong)
    return tuple(int(x) for x in m.groups()) if m else (0,)


def nap_runtime_cpp() -> list[str]:
    """Nap libstdc++/libgomp cho LightGBM tren NixOS — CHI khi that su can.

    ⚠️  CHI GOI HAM NAY O TRANG CO IMPORT LIGHTGBM/SHAP. Goi bua o trang khac se
        lam Streamlit segfault — doc phan duoi truoc khi them loi goi moi.

    VI SAO CAN: lib_lightgbm.so khai bao can libstdc++.so.6 va libgomp.so.1, nhung
    NixOS khong co /usr/lib nen `ldd` bao 'not found'. Phai nap tay bang RTLD_GLOBAL
    truoc khi import lightgbm. Tren Windows/macOS cac glob duoi day rong nen ham nay
    khong lam gi.

    VI SAO KHONG DUOC GOI VO TOI VA — LOI DA GAP NGAY 2026-08-10:
      app.py goi ham nay o dau tep, nen MOI trang deu bi nap them mot libstdc++ tu
      /nix/store bang RTLD_GLOBAL. Nhung pyarrow mang san libstdc++ rieng cua no.
      Hai ban cung nam trong mot tien trinh, ky hieu codecvt/locale phan giai cheo
      nhau, va Streamlit segfault ngay tai `pd.read_parquet`. Coredump xac nhan:

          Module libstdc++.so.6 without build-id      <- nap 2 lan
          Module libstdc++.so.6 without build-id
          #0 read_utf8_code_point      (libstdc++.so.6)
          #2 codecvt::do_in            (libstdc++.so.6)
          #3 std::ostream::_M_insert   (libstdc++.so.6)
          #4 arrow::acero::ExecPlanImpl::ToString  (libarrow_acero.so)
          #9 pyarrow._dataset.Scanner.to_table

      Trang 1 va trang 3 chi doc parquet, khong dung LightGBM — chung khong can ham
      nay, va goi vao la hong.

    VI SAO SAP XEP CHU KHONG LAY BAN DAU TIEN: thu tu glob phu thuoc thu tu doc thu
    muc cua he tep, tuc KHONG TAT DINH. May nay co 7 ban libstdc++ trong /nix/store
    (6 ban gcc-15.2.0 dung tu cac ban nixpkgs khac nhau + 1 ban gcc-15.3.0), khac
    nhau tung byte. Ca 7 deu cung cap GLIBCXX toi 3.4.34 trong khi lib_lightgbm.so
    chi can 3.4.20 — nen khong ban nao 'sai', nhung van phai chon tat dinh de moi
    lan chay hanh xu giong nhau.

    Tra ve danh sach duong dan da nap (rong neu khong nap gi).
    """
    # Neu lightgbm import duoc san thi KHONG nap gi ca — tranh dung hang libstdc++
    # thu hai vao tien trinh.
    try:
        import lightgbm  # noqa: F401
        return []
    except (ImportError, OSError):
        pass

    da_nap = []
    for ten in ("libstdc++.so.6", "libgomp.so.1"):
        ung_vien = sorted(
            set(glob.glob(f"/nix/store/*gcc*/lib/{ten}")
                + glob.glob(f"/run/current-system/sw/lib/{ten}")
                + glob.glob(f"/usr/lib*/{ten}")),
            key=lambda p: (_phien_ban(p), p),
            reverse=True,          # GCC moi nhat truoc; cung phien ban thi theo alphabet
        )
        for duong in ung_vien:
            try:
                ctypes.CDLL(duong, mode=ctypes.RTLD_GLOBAL)
                da_nap.append(duong)
                break
            except OSError:
                continue           # ban nay hong thi thu ban ke tiep, van tat dinh
    return da_nap


def load_shared_css() -> None:
    """Nap file style.css chung, tranh lap lai CSS o tung trang."""
    css = _CSS_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def header_bao_cao(tieu_de: str, phu_de: str = "", nhan_phai: str = "") -> None:
    """Dai header dau trang: logo ben trai, tieu de ke ben, nhan phu ben phai.

    VI SAO KHONG DUNG st.logo(): st.logo() ghim anh len dinh THANH SIDEBAR — do la cho
    de logo cua UNG DUNG, khong phai cua BAO CAO. Power BI va Tableau deu dat logo NAM
    TRONG khung bao cao, cung dai voi tieu de, de khi chup man hinh vung noi dung hay
    xuat PDF thi logo di theo.

    VI SAO DUNG st.image CHU KHONG NHUNG BASE64 VAO st.markdown: ban dau ham nay nhung
    logo thanh data URI trong mot khoi HTML. Cach do lam Streamlit segfault ngay lan
    render dau tren may NixOS (thu ca ban 44 KB lan ban 25 KB base64 deu chet), va khi
    server chet thi toan bo CSS bi in ra man hinh duoi dang chu. Dung thanh phan goc
    cua Streamlit thi khong con hien tuong do.
    """
    # Ba cot CAN XUNG hai ben (2 : 8 : 2) de tieu de o cot giua nam dung giua trang.
    # Neu de [1, 7, 2] thi cot giua bi lech trai, tieu de can giua theo cot van trong
    # nhu lech so voi ca trang.
    cot = st.columns([2, 8, 2])
    with cot[0]:
        if _LOGO_PATH.exists():
            # width co dinh: st.image giu dung ty le goc, khong keo gian theo be rong cot
            st.image(str(_LOGO_PATH), width=170)
    with cot[1]:
        st.markdown(f'<div class="hdr-title">{tieu_de}</div>', unsafe_allow_html=True)
        if phu_de:
            st.markdown(f'<div class="hdr-sub">{phu_de}</div>', unsafe_allow_html=True)
    with cot[2]:
        if nhan_phai:
            st.markdown(
                f'<div style="text-align:right"><span class="hdr-badge">{nhan_phai}</span></div>',
                unsafe_allow_html=True,
            )
    st.markdown('<div class="hdr-rule"></div>', unsafe_allow_html=True)
