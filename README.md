||||||| parent of 6c6fc8f (feat: add strucure project)
=======
# Du An Tot Nghiep

## Huong dan cai dat moi truong (Windows)

### Yeu cau
- Python 3.11+ da duoc cai dat: https://www.python.org/downloads/
- Kiem tra bang cach mo **Command Prompt** hoac **PowerShell** va chay:
  ```
  python --version
  ```

---

### Buoc 1: Clone hoac tai du an ve may

```bash
git clone <url-repository>
cd Du_An_Tot_Nghiep
```

---

### Buoc 2: Tao moi truong ao (.venv)

Mo **Command Prompt** hoac **PowerShell**, chay lenh sau trong thu muc du an:

```bash
python -m venv .venv
```

---

### Buoc 3: Kich hoat moi truong ao

**Command Prompt (cmd.exe):**
```cmd
.venv\Scripts\activate.bat
```

**PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

> **Luu y PowerShell:** Neu gap loi `execution policy`, chay lenh nay truoc:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Sau do kich hoat lai.

Sau khi kich hoat thanh cong, ban se thay `(.venv)` xuat hien o dau dong lenh.

---

### Buoc 4: Cai dat thu vien

```bash
pip install -r requirements.txt
```

---

### Buoc 5: Tat moi truong ao (khi xong viec)

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

- Thu muc `.venv` da co trong `.gitignore`, khong can push len git.
- Moi thanh vien trong nhom tu tao `.venv` tren may cua minh theo huong dan tren.
>>>>>>> 6c6fc8f (feat: add strucure project)
