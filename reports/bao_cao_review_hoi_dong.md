# BÁO CÁO TIẾN ĐỘ DỰ ÁN TỐT NGHIỆP - THE OUTLIERS
## HỆ THỐNG PHÂN TÍCH VÀ DỰ BÁO SẢN LƯỢNG ĐIỆN MẶT TRỜI

---

## I. VẤN ĐỀ ĐẶT RA VÀ BỐI CẢNH DỰ ÁN

Trong bối cảnh năng lượng tái tạo đang phát triển mạnh mẽ, việc vận hành hiệu quả các nhà máy điện năng lượng mặt trời (PV) đóng vai trò then chốt trong việc tối ưu hóa lợi nhuận và duy trì tuổi thọ thiết bị. Dự án của nhóm The Outliers tập trung giải quyết bài toán thực tế cho 42 trạm điện quang điện tại Úc. 

Khi tiếp cận hệ thống, nhóm nhận thấy các kỹ sư vận hành và quản lý đang phải đối mặt với một tập dữ liệu thô khổng lồ, rời rạc và chứa đầy rủi ro tiềm ẩn. Dữ liệu sản lượng điện được ghi nhận mỗi 15 phút, trong khi dữ liệu khí tượng viễn thám (từ Open-Meteo) lại cập nhật theo chu kỳ 1 giờ. Sự lệch pha này khiến việc hợp nhất dữ liệu để phân tích trở nên vô cùng khó khăn. Thêm vào đó, dữ liệu thô chứa nhiều đoạn bị khuyết (missing data), các giá trị bất thường (outliers) không rõ nguyên nhân do lỗi Inverter hoặc điều kiện môi trường bất lợi, và đặc biệt là hiện tượng dòng điện rò rỉ vào ban đêm. 

Nếu không có một hệ thống tự động để làm sạch và phân tích khối dữ liệu này, doanh nghiệp sẽ phải mất rất nhiều thời gian phân tích thủ công. Việc ra quyết định chậm trễ không chỉ gây sai số lớn trong việc tính toán doanh thu lũy kế hàng năm mà còn khiến thiết bị giảm tuổi thọ do không được bảo trì kịp thời khi xảy ra sự cố bám bẩn hay sụt giảm hiệu suất.

## II. GIẢI PHÁP ĐANG ĐƯỢC THỰC HIỆN

Để giải quyết triệt để những điểm nghẽn trên, nhóm The Outliers đã quyết định xây dựng một hệ thống Data Warehouse tập trung, tự động hóa hoàn toàn luồng xử lý dữ liệu (ETL Pipeline) theo hướng "Data-driven decision making".

Thay vì áp dụng các giải pháp làm sạch dữ liệu truyền thống bằng SQL có phần chậm chạp và cứng nhắc, nhóm đã thiết kế một kiến trúc linh hoạt. Dữ liệu từ Kaggle và API thời tiết sẽ được đẩy vào không gian lưu trữ S3 Storage (quản lý bởi DVC) và cơ sở dữ liệu PostgreSQL trên nền tảng Supabase. 

Đối với vấn đề lệch pha dữ liệu, nhóm triển khai kiến trúc "Lược đồ Thiên hà" (Galaxy Schema). Đây là một mô hình nâng cao cho phép hai bảng Fact (Sản lượng và Thời tiết) cùng tồn tại song song, chia sẻ chung các Dimensions như Địa lý, Ngày và Giờ để đồng bộ logic phân tích mà không làm méo mó bản chất gốc của dữ liệu. 

Về mặt làm sạch dữ liệu, quy trình ETL được điều phối hoàn toàn bằng Python Orchestrator. Dữ liệu sẽ đi qua vùng Staging, chuyển sang Buffer để áp dụng kỹ thuật nội suy tuyến tính (Hybrid Imputation) điền khuyết. Để xử lý các giá trị bất thường (Outliers), thay vì bắt cơ sở dữ liệu phải tính toán nặng nề, hệ thống sẽ xuất tạm dữ liệu ra định dạng Parquet, sử dụng sức mạnh của Python/Pandas với thuật toán Rolling IQR để quét và phát hiện nhiễu. Sau đó, hệ thống mới nạp lại các "cờ đánh dấu" (Outlier Flags) ngược vào cơ sở dữ liệu.

## III. KẾT QUẢ CỤ THỂ CHO ĐẾN THỜI ĐIỂM HIỆN TẠI

Tính đến thời điểm báo cáo (giai đoạn Scrum 6/7), nhóm đã triển khai thành công phần lõi của hệ thống và bắt đầu thu hoạch được những kết quả đáng kể:

**1. Về hạ tầng và kỹ thuật:**
- Nhóm đã xây dựng hoàn chỉnh và đưa vào vận hành Galaxy Schema trên hệ quản trị cơ sở dữ liệu Supabase. 
- Hệ thống Pipeline ETL tự động đã chạy ổn định từ đầu tới cuối (Extract, Cleanse, Outlier Detection, Load vào Data Warehouse). 
- Công cụ DVC (Data Version Control) đã được tích hợp trơn tru, giúp nhóm lưu trữ các file trung gian dung lượng lớn trên S3 mà không làm quá tải kho lưu trữ mã nguồn Git.

**2. Về Insight phân tích được:**
- **Hiện tượng suy hao do nhiệt (Thermal Degradation):** Dữ liệu sạch đã chỉ ra một sự thật thú vị rằng: Bức xạ mặt trời cao nhất vào buổi trưa không đồng nghĩa với sản lượng điện cao nhất. Hiệu suất các tấm pin thực tế đã giảm mạnh khi nhiệt độ môi trường vượt ngưỡng 25°C.
- **Dấu hiệu bảo trì dự đoán (Predictive Maintenance):** Hệ thống đã phát hiện ra các thời điểm bức xạ nắng rất cao nhưng sản lượng thực tế lại sụt giảm so với đường cơ sở (Baseline). Đây là tín hiệu rõ ràng cảnh báo tấm pin đang bị che khuất, bám bẩn hoặc Inverter đang gặp trục trặc, cần điều phối kỹ sư kiểm tra ngay.
- **Lọc bỏ dòng điện rò rỉ:** Phân tích cho thấy có dòng điện rò rỉ và nhiễu tín hiệu trong khung giờ từ 18h tối đến 5h sáng hôm sau. Nhóm đã cấu hình Pipeline chủ động nhận diện và loại bỏ phần nhiễu này để đảm bảo độ chính xác của các chỉ số tài chính.

*Lưu ý: Do dự án đang trong tiến trình phát triển, hạng mục xây dựng giao diện Dashboard cuối cùng (trên Tableau/PowerBI) và việc huấn luyện các mô hình Machine Learning (ARIMA, Prophet) để dự báo sản lượng tương lai đang trong quá trình chuẩn bị dữ liệu (tại ML Mart & BI Mart) và sẽ sớm được hoàn thiện trong những giai đoạn tiếp theo.*

## IV. THUẬN LỢI, KHÓ KHĂN VÀ BÀI HỌC KINH NGHIỆM

**1. Những thuận lợi trong quá trình triển khai:**
Việc thống nhất áp dụng các công nghệ hiện đại ngay từ đầu như Supabase và DVC đã giúp nhóm giải quyết nhanh chóng bài toán lưu trữ lớn. Bên cạnh đó, việc quyết định tách logic tính toán phức tạp (Rolling IQR) ra khỏi SQL và giao cho thư viện Pandas (Python) xử lý trên file Parquet đã tối ưu hóa được rất nhiều thời gian chạy Pipeline, giúp hệ thống không bị nghẽn cổ chai.

**2. Những khó khăn đang gặp phải:**
Thử thách lớn nhất mà nhóm phải đối mặt là sự khác biệt về chu kỳ thời gian (15 phút của sản lượng so với 1 giờ của thời tiết). Đã có những thời điểm, việc cố gắng nhồi nhét hai loại dữ liệu này vào chung một bảng Fact (mô hình Star Schema) gây ra tình trạng bùng nổ dữ liệu trùng lặp hoặc sai lệch ngữ nghĩa. Nhóm đã phải mất nhiều thời gian nghiên cứu và đập đi xây lại bằng kiến trúc Galaxy Schema để giải quyết triệt để vấn đề này.
Khó khăn thứ hai là việc cấu hình quy trình làm việc nhóm (Git flow) và đồng bộ DVC giữa các thành viên. Quá trình chia sẻ các tập tin dữ liệu lớn trong giai đoạn đầu gặp không ít lỗi xung đột (conflict) trước khi mọi người quen với quy trình.

**3. Hướng phát triển tiếp theo:**
Đứng trước những thành quả ban đầu, nhóm đã vạch ra lộ trình rõ ràng cho giai đoạn tới:
- Bắt tay vào xây dựng và tinh chỉnh các mô hình dự báo học máy (Machine Learning) để có thể phán đoán chính xác sản lượng điện trong tương lai.
- Chuyển giao số liệu từ BI Mart sang hệ thống trực quan hóa nhằm thiết kế nên những Dashboard thân thiện, giúp người dùng cuối chỉ cần vài cú click chuột là có thể nắm bắt được tình hình vận hành toàn trạm. 

---
*Tài liệu được chuẩn bị cho buổi Review Hội đồng tiến độ dự án (Pre-defense Review).*
