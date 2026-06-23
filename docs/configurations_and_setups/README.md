# CẤU HÌNH, CÀI ĐẶT VÀ KIẾN TRÚC KỸ THUẬT

Thư mục `configurations_and_setups` tập trung lưu trữ các tài liệu mang tính chất "kỹ thuật hạ tầng", định hướng phát triển và triển khai hệ thống dự án The Outliers. 

Đây là thư mục quan trọng dành cho **Kỹ sư dữ liệu (Data Engineer)** và **Quản trị viên hệ thống (Admin)**.

---

## DANH SÁCH TÀI LIỆU

1. **[supabase_connection.md](supabase_connection.md):** 
   - Hướng dẫn thiết lập Supabase Database và Storage.
   - Giải thích chi tiết thiết kế Data Warehouse theo **Galaxy Schema** (Các bảng Fact và Dimension, cách liên kết khóa).
2. **[HUONG_DAN_CHAY_CLOUD.md](HUONG_DAN_CHAY_CLOUD.md):** 
   - Cẩm nang hướng dẫn đưa dự án lên Cloud, cấu hình DVC (Data Version Control), và điều phối pipeline ở môi trường remote/production.
3. **[REFACTOR_REPORT.md](REFACTOR_REPORT.md) & [2026_06_21_bao_cao_refactor_NgoTanDat.pdf](2026_06_21_bao_cao_refactor_NgoTanDat.pdf):** 
   - Báo cáo quy trình tái cấu trúc mã nguồn dự án (Refactor) để mã sạch hơn, hướng đối tượng và dễ mở rộng.
4. **[2026_06_21_BaoCaoDVC_NgoTanDat.pdf](2026_06_21_BaoCaoDVC_NgoTanDat.pdf):** 
   - Hướng dẫn tích hợp và vận hành DVC để quản lý dữ liệu khổng lồ của dự án thay vì đẩy lên Git thông thường.
5. **[Quy chuẩn Code (Coding Rule)](2026_06_05_coding_rule_TanDat.pdf):** 
   - Bộ quy tắc viết mã (PEP8, Naming Conventions) dành cho lập trình viên.
6. **[WINDOWS_SETUP.md](WINDOWS_SETUP.md):** 
   - Sổ tay cấu hình môi trường lập trình tối ưu trên hệ điều hành Windows.

> **Lưu ý:** Nếu bạn là lập trình viên mới gia nhập, hãy đọc `supabase_connection.md` và Cẩm nang cấu hình môi trường trước khi đọc bất kỳ dòng code nào.
