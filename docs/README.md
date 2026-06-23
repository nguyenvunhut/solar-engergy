# TÀI LIỆU BÁO CÁO VÀ SCRUM DỰ ÁN

Thư mục `docs/` là nơi lưu trữ toàn bộ hồ sơ thiết kế, tài liệu nghiệp vụ, và các báo cáo được tổng hợp theo các chu kỳ (Scrum/Sprint) trong khuôn khổ đồ án tốt nghiệp. 

Việc theo dõi các tài liệu này giúp Giám thị hoặc người tiếp nhận dự án hiểu rõ quá trình ra quyết định, nguyên tắc kinh doanh và lộ trình hoàn thiện dự án.

---

## TỔ CHỨC THƯ MỤC

### `configurations_and_setups/`
Các tài liệu hướng dẫn liên quan đến thiết lập kỹ thuật, quy chuẩn code (Coding Rules), quy chuẩn Commit, hướng dẫn deploy Cloud (Supabase/Docker) và giải thích thiết kế Data Warehouse.
*Xem chi tiết tại: [README của Cấu hình](configurations_and_setups/README.md)*

### `scrum_5_pipeline_foundation/`
Giai đoạn thiết lập nền tảng. Bao gồm tài liệu crawl dữ liệu thô, nạp dữ liệu Staging, đối soát độ vẹn toàn (Data Integrity) và báo cáo cấu trúc kỹ thuật nạp Kho Dữ Liệu (DW).

### `scrum_6_business_logic_eda/`
Giai đoạn phân tích và định nghĩa logic kinh doanh. Đây là trung tâm của việc xây dựng logic cho dự án:
- Tài liệu Từ điển Dữ liệu (Data Dictionary).
- Lược đồ Logical / Physical Model.
- Báo cáo thuật toán và cơ sở toán học xử lý Outlier / Missing Data.
- Định nghĩa các chỉ số kinh doanh (KPIs/Measures) cho hệ thống BI Mart.

### `scrum_7_visualization_forecasting/`
Giai đoạn trực quan hóa và mô hình học máy. Các kế hoạch làm EDA chuyên sâu, hướng dẫn triển khai Machine Learning (Dự báo Baseline) và xây dựng Dashboard biểu đồ.

### `scrum_8_project_delivery_defense/`
Giai đoạn đóng gói sản phẩm, chuẩn bị tài liệu bảo vệ và các sổ tay chuyển giao hệ thống.
