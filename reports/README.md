# TÀI LIỆU BÁO CÁO VÀ HỆ THỐNG SƠ ĐỒ KỸ THUẬT (REPORTS)

Thư mục `reports/` chứa toàn bộ mã nguồn báo cáo tốt nghiệp viết bằng LaTeX, các tệp tài liệu PDF đã biên dịch, cùng hệ thống sơ đồ kiến trúc và biểu đồ phân tích phục vụ bảo vệ đồ án.

---

## 1. CẤU TRÚC MÃ NGUỒN BÁO CÁO LATEX

Báo cáo chính được biên soạn theo cấu trúc module hóa chuẩn học thuật:

| Tệp / Thư mục | Vai trò và Nội dung Chi tiết |
| :--- | :--- |
| **`DATN_REPORT_FINAL_02.tex`** | Tệp điều phối chính (Main TeX file) — định nghĩa cấu hình trang, gói thư viện, môi trường toán học, định dạng bảng biểu và gọi các chương con. |
| **`DATN_REPORT_FINAL_02.pdf`** | Bản in PDF hoàn chỉnh sau khi biên dịch bằng công cụ `latexmk` / `xelatex`. |
| **`Section1.tex`** | **Chương 1: Tổng quan Đề tài & Bối cảnh Miền Nghiệp vụ** — giới thiệu mạng lưới 42 trạm phát điện mặt trời tại La Trobe University ($P_{\text{stc}} = 2.428\,\text{kWp}$), cơ sở vật lý quang điện và các chuẩn đo lường quốc tế (IEC 61724-1). |
| **`Section2.tex`** | **Chương 2: Khảo sát Hiện trạng & Thu thập Dữ liệu** — phân tích tập dữ liệu viễn thám $2.73\text{M}$ dòng 15p và $850\text{k}$ dòng khí tượng ERA5-Land. |
| **`Section3.tex`** | **Chương 3: Kiến trúc Kho Dữ liệu & Tiền xử lý** — mô hình hóa Lược đồ Thiên hà (Galaxy Schema), thuật toán Điền khuyết Nhân quả 4 cấp độ và xử lý lệch pha thời gian Floor-Hour Matching. |
| **`Section4.tex`** | **Chương 4: Nhận diện Dị thường Vận hành** — thiết kế mô hình lai CART $\to$ GMM $\to$ Isolation Forest kết hợp hệ thống 5 rào chắn vật lý ($104$ giờ ngoại lai, $0{,}45\%$). |
| **`Section5.tex`** | **Chương 5: Xây dựng Tầng Phục vụ BI Mart & Tableau** — tối ưu hóa Materialized View `bi_mart.mv_bi_mart_hourly_measures` nén 1 giờ và thiết kế Bộ 3 Dashboard quản trị (Executive Overview, Efficiency & Loss, Anomaly & CBM). |
| **`Section6.tex`** | **Chương 6: Mô hình Học máy Dự báo Công suất** — triển khai mô hình LightGBM Regressor với hàm mất mát Huber Loss, kỹ nghệ 52 đặc trưng và dự báo đa bước H1 ($15\text{p}$, WAPE = $17{,}74\%$) & H4 ($60\text{p}$, WAPE = $22{,}62\%$). |
| **`Section7.tex`** | **Chương 7: Đánh giá Kết quả & Kết luận** — tổng kết chỉ số kỹ thuật, đánh giá hiệu quả kinh tế - kỹ thuật và đề xuất hướng phát triển. |
| **`appendix.tex`** | Phụ lục kỹ thuật — bảng tra cứu hằng số, mã lỗi vận hành và cấu trúc bảng CSDL. |
| **`references.bib`** | Danh mục tài liệu tham khảo học thuật (IEEE, Solar Energy, ScienceDirect, WMO, ECMWF). |

---

## 2. HỆ THỐNG SƠ ĐỒ VÀ HÌNH ẢNH TRỰC QUAN

- **`diagrams/`**: Chứa tài liệu tổng hợp sơ đồ hệ thống [`data_pipeline.md`](diagrams/data_pipeline.md) và các ảnh sơ đồ luồng dữ liệu kiến trúc 6 lớp, mô hình hóa DWH và đường ống Machine Learning.
- **`figures/` & `images/`**: Chứa biểu đồ phân rã suy hao nhiệt độ, ma trận phân bố bức xạ, kết quả giải thích mô hình SHAP và ảnh chụp giao diện Tableau Dashboards.
- **`gmm_if_report/`**: Báo cáo thống kê và trực quan hóa chi tiết các trường hợp ngoại lai được phát hiện bởi thuật toán GMM-IF.
- **`official_tableau/` & `tableau_theme/`**: Tệp workbook Tableau (`.twbx`), bảng màu chuẩn và asset thiết kế giao diện BI.

---

## 3. HƯỚNG DẪN BIÊN DỊCH BÁO CÁO LATEX

Yêu cầu môi trường đã cài đặt TeX Live hoặc MiKTeX (hỗ trợ tiếng Việt qua XeLaTeX hoặc pdfLaTeX):

```bash
# Biên dịch tài liệu chính
xelatex -synctex=1 -interaction=nonstopmode DATN_REPORT_FINAL_02.tex
bibtex DATN_REPORT_FINAL_02
xelatex -synctex=1 -interaction=nonstopmode DATN_REPORT_FINAL_02.tex
xelatex -synctex=1 -interaction=nonstopmode DATN_REPORT_FINAL_02.tex
```
