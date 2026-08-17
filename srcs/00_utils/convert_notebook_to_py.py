#!/usr/bin/env python3
"""Chuyen code cell cua notebooks/refactor/*.ipynb thanh file .py chay duoc,
KHONG sua notebook goc. Moi notebook -> 1 file .py, toan bo code cell duoc gop
vao trong 1 ham run_stage() theo dung thu tu, giu nguyen 100% logic (khong go
lai tay de tranh sai sot). Markdown cell duoc giu lai duoi dang comment '# ##'
ngay truoc doan code tuong ung, de doc file .py van hieu duoc dang di cua tung
buoc.

Dung: python srcs/00_utils/convert_notebook_to_py.py
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_DIR = PROJECT_ROOT / "notebooks" / "refactor"
OUTPUT_DIR = PROJECT_ROOT / "srcs" / "05_machine_learning" / "refactor_pipeline"

# Thu tu pipeline that (theo README PLAN, khong phai thu tu bang chu cai file).
STAGE_ORDER = [
    "01_reindex_mask_outlier",
    "02_split_time_series",
    "03_1_features_time",
    "03_2_features_spatial",
    "03_3_features_aggregate",
    "04_vif_diagnostics",
    "05_select_features",
    "06_1_train_mae",
    "06_2_train_huber",
    "06_3_train_mse",
    "06_0b_baseline_prophet",
    "07_final_test",
    "08_explainable_ai",
    "09_kiem_chung_tre_pha",
]


def markdown_to_comment(src: str) -> str:
    lines = src.splitlines()
    return "\n".join(f"# {l}" if l.strip() else "#" for l in lines)


def convert_one(notebook_name: str) -> Path:
    nb_path = NOTEBOOK_DIR / f"{notebook_name}.ipynb"
    nb = json.loads(nb_path.read_text(encoding="utf-8"))

    body_parts: list[str] = []
    for cell in nb["cells"]:
        src = "".join(cell["source"])
        if not src.strip():
            continue
        if cell["cell_type"] == "markdown":
            body_parts.append(markdown_to_comment(src))
        else:
            body_parts.append(src)
    body = "\n\n".join(body_parts)

    # Thut le toan bo body vao trong ham run_stage(), giu nguyen indentation
    # tuong doi cua tung dong code.
    indented = "\n".join(("    " + l if l.strip() else "") for l in body.splitlines())

    func_name = "run_stage"
    header = f'''"""File nay duoc TU DONG SINH RA tu notebook goc, KHONG sua notebook.

Nguon: notebooks/refactor/{notebook_name}.ipynb
Sinh boi: srcs/00_utils/convert_notebook_to_py.py
Toan bo logic ben trong ham {func_name}() la nguyen van cell code cua notebook,
gop lai theo dung thu tu, khong chinh sua noi dung. Neu can sua logic, sua o
notebook goc roi chay lai script convert nay, KHONG sua truc tiep file .py.
"""
from __future__ import annotations


def {func_name}():
{indented}


if __name__ == "__main__":
    {func_name}()
'''
    out_path = OUTPUT_DIR / f"{notebook_name}.py"
    out_path.write_text(header, encoding="utf-8")
    return out_path


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in STAGE_ORDER:
        out = convert_one(name)
        print(f"- {name}.ipynb -> {out.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
