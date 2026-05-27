# Du An Tot Nghiep

## Cai dat moi truong

> Yeu cau: **Python 3.11+** da duoc cai san tren may.

---

### Buoc 1: Tao moi truong ao

**Windows:**
```cmd
py -3.11 -m venv .venv
```

**Linux / macOS:**
```bash
python3.11 -m venv .venv
```

---

### Buoc 2: Kich hoat moi truong ao

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

> Neu PowerShell bao loi, chay lenh nay truoc roi kich hoat lai:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

Kich hoat thanh cong se thay `(.venv)` o dau dong lenh.

---

### Buoc 3: Cai dat thu vien

```bash
pip install -r requirements.txt
```
---
### Buoc 4: Tat moi truong ao (khi xong viec)

```bash
deactivate
```

---

### Cau truc du an

```
Du_An_Tot_Nghiep/
├── data/
│   ├── raw/          <- Du lieu goc, khong chinh sua
│   ├── interim/      <- Du lieu trung gian da qua xu ly
│   ├── processed/    <- Du lieu cuoi cung dung de modeling
│   └── external/     <- Du lieu tu nguon ben ngoai
├── notebooks/        <- Jupyter notebooks
├── models/           <- Model da train
├── reports/
│   └── figures/      <- Bieu do, hinh anh bao cao
├── docs/             <- Tai lieu du an
├── references/       <- Tai lieu tham khao
├── du_an_tot_nghiep/ <- Package Python chinh
│   ├── config.py
│   ├── dataset.py
│   ├── features.py
│   ├── plots.py
│   └── modeling/
│       ├── train.py
│       └── predict.py
├── requirements.txt
└── pyproject.toml
```

---

### Luu y

- Thu muc `.venv` khong duoc push len git (da co trong `.gitignore`).
- Moi thanh vien tu tao `.venv` tren may cua minh theo huong dan tren.
