# PHÂN HỆ XÂY DỰNG DATA MARTS (04_BUILD_DATA_MARTS)

Phân hệ `srcs/04_build_data_marts/` chịu trách nhiệm tạo ra 2 nhánh phục vụ dữ liệu chuyên biệt từ Kho Dữ liệu Trung tâm (DWH Core): **Nhánh BI Data Mart** phục vụ Tableau Dashboard và **Nhánh ML Data Mart** phục vụ mô hình học máy.

---

## 1. CÁC MODULE VÀ NHÁNH DỮ LIỆU

### 1.1. Nhánh BI Data Mart (`01_build_bi_mart.py`, `05_mv_bi_mart.py`)
- Khởi tạo Materialized View `bi_mart.mv_bi_mart_hourly_measures`.
- **Tối ưu hóa độ hạt:** Nén $2.73\text{M}$ dòng chu kỳ 15 phút thành $\sim 683\text{k}$ dòng chu kỳ 1 giờ.
- **Tiền tính toán chỉ số:** Tính sẵn $PR_{\text{actual}}$, $PR_{\text{adjusted}}$, $E_{\text{expected}}$, $Loss_{\text{temp}}$.
- **Hiệu năng:** Dung lượng view nén $<80\,\text{MB}$, thời gian phản hồi truy vấn $<100\,\text{ms}$, giúp Tableau Desktop mở dashboard trong $<2\,\text{giây}$.

### 1.2. Nhánh ML Data Mart (`02_build_ml_mart.py`)
- Khởi tạo bảng cơ sở `ml_mart.ml_mart_base` và Feature Store.
- Trích xuất và gắn kết 52 đặc trưng trễ chuỗi thời gian, thông số thiên văn học (góc nâng mặt trời $\alpha$, góc thiên đỉnh) và biến tương tác vi khí hậu.

### 1.3. Kiểm toán Chất lượng (`04_qa_qc_fixed.py`)
- Kiểm tra tính nhất quán số học, kiểm toán rò rỉ dữ liệu khí tượng và xác nhận toàn vẹn các trường định danh.

---

## 2. HƯỚNG DẪN THỰC THI

```bash
# Xây dựng BI Data Mart:
python srcs/04_build_data_marts/05_mv_bi_mart.py

# Xây dựng ML Data Mart:
python srcs/04_build_data_marts/02_build_ml_mart.py

# Hoặc thực thi thông qua Orchestrator:
python srcs/06_run_pipeline/main.py --stage bimarts
python srcs/06_run_pipeline/main.py --stage mlmarts
```
