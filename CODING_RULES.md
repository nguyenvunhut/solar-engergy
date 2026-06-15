# Coding Standards — The Outliers

Bộ quy tắc chung áp dụng cho toàn bộ dự án **The Outliers**. Tất cả thành viên phải đọc và tuân thủ trước khi commit code.

---

## 1. Quy tắc Đặt tên (Naming)

| Loại đối tượng | Quy tắc | Ví dụ |
| :--- | :--- | :--- |
| **Biến & Hàm** | `snake_case` | `load_data`, `site_id` |
| **Class (Lớp)** | `PascalCase` | `SolarSite`, `WeatherLoader` |
| **Hằng số** | `UPPER_CASE` | `BUCKET_NAME`, `DB_HOST` |
| **File Python** | `snake_case` | `load_01_dims.py` |
| **Tập tin tài liệu** | `YYYY_MM_DD_content_Author.ext` | `2026_05_25_schema_design_TanDat.tex` |

> [!IMPORTANT]
> **Tên phải có ý nghĩa:** Không sử dụng các tên biến chung chung như `x`, `df2`, `tmp`.

---

## 2. Định dạng Code (Code Formatting)

*   **Thụt lề (Indentation):** Sử dụng **4 spaces** cho thụt lề. Không sử dụng tab hoặc thụt lề 2/3 spaces.
*   **Độ dài dòng (Line Length):** Tối đa **88 ký tự** (theo tiêu chuẩn Black).
*   **Auto-Format & Linting:** Sử dụng `ruff` để tự động định dạng và kiểm tra lỗi tĩnh:
    ```bash
    # Định dạng code
    ruff format src/
    
    # Kiểm tra lỗi tĩnh
    ruff check src/
    ```

---

## 3. Quy tắc Import

Các khối import phải được sắp xếp theo thứ tự, cách nhau bởi **1 dòng trắng**:

1.  **Thư viện chuẩn (Standard Library):**
    ```python
    import os
    from pathlib import Path
    ```
2.  **Thư viện bên thứ ba (Third-party Library):**
    ```python
    import pandas as pd
    import psycopg2
    ```
3.  **Module nội bộ dự án (Local Module):**
    ```python
    from src.config import DB_HOST
    ```

> [!WARNING]
> Tuyệt đối **không** dùng `import *`.

---

## 4. Thiết kế Hàm và Lớp (Functions & Classes)

*   **Single Responsibility (SRP):** Mỗi hàm hoặc lớp chỉ làm duy nhất một việc.
*   **Type Hints:** Sử dụng gợi ý kiểu dữ liệu cho tham số đầu vào và giá trị trả về của hàm:
    ```python
    def load_csv(path: str) -> pd.DataFrame:
        """Load raw CSV file from given path."""
        return pd.read_csv(path)
    ```
*   **Docstring:** Viết mô tả ngắn gọn cho các hàm quan trọng.
*   **Độ dài hàm:** **Tránh hàm dài hơn 30 dòng**. Nếu hàm quá dài, cần tách thành các hàm nhỏ hơn.

---

## 5. Xử lý lỗi (Exception Handling)

*   Bắt lỗi cụ thể, không sử dụng khối `except:` chung chung hoặc `except Exception:`.
*   Không nuốt lỗi im lặng (`pass` trong block except).

```python
# SAI
try:
    load_data()
except:
    pass

# ĐÚNG
try:
    load_data()
except FileNotFoundError as e:
    print(f"File not found: {e}")
    raise
```

---

## 6. Không lặp code (DRY - Don't Repeat Yourself)

*   Nếu một đoạn logic được sử dụng nhiều hơn 1 lần, cần tách thành hàm dùng chung.
*   Không sao chép-dán (copy-paste) các khối code giữa các tập tin khác nhau.

---

## 7. Jupyter Notebook

*   **Đánh số ô (Cell):** Đánh số cell theo thứ tự logic, đảm bảo có thể chạy từ trên xuống dưới không có lỗi.
*   **Tên Notebook:** Đặt theo cấu trúc `XX_tên_notebook.ipynb` (ví dụ: `01_eda_solar_generation.ipynb`).
*   **Dọn dẹp Output:** Xóa toàn bộ output rác (print thừa, lỗi stack trace) trước khi commit.

---

## 8. Quy chuẩn Commit Message

Tuân thủ quy chuẩn Angular commit:
```
<type>(<scope>)[SCRUM-KEY](<mô tả ngắn>)
```

*   **Type:**
    *   `feat`: Thêm tính năng mới
    *   `fix`: Sửa lỗi
    *   `refactor`: Tái cấu trúc code (không đổi tính năng)
    *   `chore`: Công việc phụ (cấu hình, tài liệu, sprint)
*   **Ví dụ:**
    ```
    feat(etl)[scrum-40](add night noise filter to transform pipeline)
    ```

> [!TIP]
> Bạn có thể sử dụng công cụ hỗ trợ commit bằng cách chạy lệnh:
> `python commit_helper.py` hoặc `.venv\Scripts\python commit_helper.py`

---

## 9. Thiết kế Hướng đối tượng (OOP - Tùy chọn)

Sử dụng lớp (class) khi logic phức tạp, có lưu trạng thái (state), hoặc cần tái sử dụng nhiều lần. Đối với các script ETL đơn giản chạy một lần, chỉ cần hàm là đủ.

*   **Khi nào nên dùng:**
    *   *Script ETL chạy 1 lần:* Dùng **Hàm**
    *   *Connector tái sử dụng (DB, MinIO):* Dùng **Class**
    *   *Model Machine Learning:* Dùng **Class**
    *   *Nhiều hàm dùng chung trạng thái:* Dùng **Class**
*   **Nguyên tắc:**
    *   **Single Responsibility (SRP):** Tách rõ trách nhiệm cho các class khác nhau (ví dụ: `DataLoader`, `DataCleaner`).
    *   Sử dụng `@property` thay vì getter/setter thủ công.
    *   **Ưu tiên composition hơn inheritance:** Kết hợp các thực thể thay vì kế thừa.
    *   **Quy tắc gạch dưới:** `_var` cho nội bộ (internal/protected), `__var` cho name mangling.

---

## 10. Những điều Tuyệt đối KHÔNG LÀM (Strict Don'ts)

1.  **Không commit trực tiếp lên nhánh `main`.**
2.  **Không push các tệp cấu hình chứa khóa bảo mật (`.env`), môi trường ảo (`.venv`), hoặc tệp dữ liệu dung lượng lớn (`.csv`, `.xlsx`).**
3.  **Không sử dụng `import *`.**
4.  **Không hardcode thông tin đăng nhập, token bảo mật, hoặc URL có chứa mật khẩu trong mã nguồn.**
