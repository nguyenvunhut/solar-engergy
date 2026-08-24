# QUẢN LÝ TẬP DỮ LIỆU VÀ PHIÊN BẢN (DATA ARCHITECTURE)

Thư mục `data/` chứa các tầng dữ liệu của dự án từ nguồn thô (Raw) đến các tập dữ liệu đã làm sạch (Processed) và bảng cơ sở phục vụ huấn luyện mô hình (ML Mart).

---

## 1. CẤU TRÚC PHÂN TẦNG DỮ LIỆU

```
data/
├── raw/                 # Dữ liệu nguồn thô ban đầu (Bảo toàn nguyên bản)
│   ├── solar_gen/       # Dữ liệu viễn thám IoT 42 trạm phát (2.73M dòng • 15 phút)
│   └── weather/         # Dữ liệu tái phân tích khí tượng ERA5-Land (850k dòng • 1 giờ)
├── processed/           # Dữ liệu trung gian qua các bước tiền xử lý
│   ├── imputed/         # Dữ liệu sau khi điền khuyết 4 cấp độ
│   └── outlier_flagged/ # Dữ liệu sau khi gắn nhãn dị thường GMM-IF và 5 rào chắn vật lý
├── mlmart_base/         # Bảng cơ sở hoàn chỉnh phục vụ Machine Learning
│   └── v3_final_cleaned.parquet # 2.73M dòng đã căn chỉnh sàn giờ và kiểm toán nhân quả
└── model/               # Thư mục lưu trữ artifact mô hình đã huấn luyện
```

---

## 2. QUY CHUẨN DỮ LIỆU VÀ ĐỘ HẠT

| Tầng Dữ Liệu | Độ Hạt Thời Gian | Quy Mô Bản Ghi | Định Dạng Lưu Trữ | Vai Trò Kỹ Thuật |
| :--- | :---: | :---: | :---: | :--- |
| **`raw/`** | 15 phút / 1 giờ | $\sim 3{,}58\text{M}$ bản ghi | CSV / S3 Object | Dữ liệu đối chứng ban đầu, phục vụ nạp tầng Staging. |
| **`processed/`** | 15 phút | $2.731.946$ bản ghi | CSV / Parquet | Dữ liệu sạch, đã xử lý $1.536.000$ ô khuyết và lọc dị thường. |
| **`mlmart_base/`** | 15 phút | $2.731.946$ bản ghi | Parquet (Snappy) | Tầng cơ sở phục vụ trích xuất 52 đặc trưng và huấn luyện mô hình. |

---

## 3. QUẢN LÝ PHIÊN BẢN DỮ LIỆU BẰNG DVC

Do dung lượng tập dữ liệu lớn, toàn bộ các tệp trong `data/` được theo dõi và đồng bộ phiên bản thông qua **DVC (Data Version Control)** và lưu trữ trên **Supabase Storage S3**:

```bash
# Kéo dữ liệu phiên bản mới nhất từ S3 Remote:
dvc pull

# Đẩy dữ liệu mới cập nhật lên S3 Remote:
dvc push
```
