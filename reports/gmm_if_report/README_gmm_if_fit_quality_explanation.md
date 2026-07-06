# Giải thích kết quả GMM-IF Fit Quality Metrics

File này dùng để giải thích các chỉ số audit của thuật toán outlier detection GMM-IF trong pipeline. Đây là bài toán không có nhãn outlier thủ công, vì vậy không thể dùng các metric supervised như accuracy, precision, recall, F1 theo nghĩa truyền thống. Thay vào đó, pipeline dùng nhóm metric kiểm tra độ ổn định và độ hợp lý của mô hình không giám sát.

## 1. Kết luận ngắn

Kết quả hiện tại đủ ổn để bảo vệ ở mức demo/kỹ thuật:

- GMM hội tụ `100%` trên toàn bộ 42 site.
- Isolation Forest giữ đúng contamination khoảng `3%` trên từng site.
- Decision Tree chia mỗi site thành khoảng `19–29` leaf segments, không phải chia quá ít.
- GMM và IF không bắt trùng quá nhiều; Jaccard agreement khoảng `6.4%–16.7%`, cho thấy bước fusion `GMM ∧ IF` có tác dụng lọc false-positive.
- Các chỉ số BIC/AIC/log-likelihood được lưu để audit chất lượng fit của GMM theo từng site/segment.

Không nên trình bày nguyên bảng dài trong slide chính. Bảng này nên để trong appendix hoặc log kỹ thuật. Slide chính chỉ nên lấy các dòng tổng hợp.

## 2. Vì sao không dùng accuracy / precision / recall?

Outlier detection ở đây là bài toán không giám sát. Dataset không có cột nhãn do con người xác nhận:

```text
normal / outlier
```

Vì vậy nếu báo cáo accuracy, precision, recall, F1 thì sẽ không có cơ sở, trừ khi tự tạo label thủ công hoặc có chuyên gia xác nhận từng điểm bất thường.

Thay vào đó, pipeline kiểm tra mô hình qua 3 hướng:

1. Decision Tree segmentation có chia dữ liệu thành các vùng hợp lý không.
2. GMM có fit ổn định trong từng segment không.
3. Isolation Forest và GMM có đồng thuận ở mức hợp lý không, trước khi đưa ra final flag.

## 3. Ý nghĩa từng cột

### `rows_day`

Số dòng daytime được dùng để đánh giá outlier. Night-time được tách riêng vì sản lượng điện mặt trời ban đêm bằng 0 là trạng thái vật lý bình thường, không nên đưa vào đánh giá outlier như ban ngày.

Ví dụ:

```text
sitekey=1 rows_day=42980
```

Nghĩa là site 1 có 42,980 dòng ban ngày được đưa vào mô hình.

### `tree_leaf_segments`

Số leaf segment do Decision Tree tạo ra cho từng site.

Kết quả hiện tại:

```text
min khoảng 19
max khoảng 29
```

Diễn giải:

Decision Tree không chia dữ liệu quá thô. Mỗi site được chia thành nhiều vùng vận hành theo giờ trong ngày, mùa, bức xạ và mức năng lượng kỳ vọng. Đây là bước làm cho GMM fit trên từng phân phối nhỏ hơn thay vì fit một phân phối lớn cho toàn bộ site.

Câu trả lời nếu bị hỏi:

> Decision Tree không dùng để dự đoán outlier trực tiếp. Nó dùng để phân đoạn dữ liệu PV thành các vùng vận hành tương đối đồng nhất. Sau đó GMM mới fit trên từng segment.

### `gmm_segments_fit`

Số segment thực sự được fit GMM.

Trong kết quả hiện tại, `gmm_segments_fit` bằng với `tree_leaf_segments` ở tất cả site.

Diễn giải:

Không có segment nào bị bỏ qua do thiếu dữ liệu hoặc lỗi fit. Đây là dấu hiệu pipeline ổn định.

### `gmm_converged_pct`

Tỷ lệ GMM hội tụ sau khi fit.

Kết quả hiện tại:

```text
100% trên toàn bộ 42 site
```

Đây là chỉ số quan trọng nhất để chứng minh GMM không bị lỗi fit.

Câu trả lời nếu bị hỏi:

> Tất cả GMM theo segment đều hội tụ 100%, nên phần fit Gaussian Mixture ổn định. Nếu chỉ số này thấp, mô hình có nguy cơ không đáng tin vì nhiều segment không hội tụ.

### `gmm_weighted_avg_log_likelihood`

Log-likelihood trung bình có trọng số theo số dòng trong segment.

Ý nghĩa:

- Giá trị càng cao thì GMM fit dữ liệu trong các segment càng tốt.
- Giá trị có thể âm hoặc dương, vì đây là log density của biến liên tục.
- Không nên so sánh tuyệt đối giữa các site một cách máy móc, vì phân phối residual và scale từng site khác nhau.

Diễn giải đúng:

> Chỉ số này dùng để audit nội bộ chất lượng fit của GMM theo từng site. Nó không phải threshold outlier và không phải accuracy.

### `gmm_weighted_bic_per_row`

BIC trung bình trên mỗi dòng, có trọng số theo số dòng trong segment.

Ý nghĩa:

- BIC thấp hơn thường tốt hơn vì nó cân bằng giữa độ fit và độ phức tạp của mô hình.
- Dùng để kiểm tra GMM không fit quá phức tạp một cách vô lý.
- Nên dùng để so sánh các cấu hình GMM khác nhau hơn là kết luận site A tốt hơn site B tuyệt đối.

Câu trả lời nếu bị hỏi:

> BIC/AIC được lưu để kiểm soát chất lượng fit và độ phức tạp của GMM. Vì đây là unsupervised detection, BIC/AIC là metric phù hợp hơn accuracy khi chưa có nhãn.

### `gmm_weighted_aic_per_row`

AIC trung bình trên mỗi dòng, tương tự BIC nhưng phạt độ phức tạp nhẹ hơn.

Ý nghĩa:

- AIC thấp hơn thường tốt hơn.
- Dùng song song với BIC để audit độ hợp lý của GMM.

### `if_score_iqr`

Khoảng tứ phân vị của Isolation Forest anomaly score.

Ý nghĩa:

- Nếu IQR quá nhỏ, anomaly score gần như phẳng, IF khó phân biệt điểm bình thường và điểm bất thường.
- Kết quả hiện tại khoảng `0.04–0.057`.
- Điều này cho thấy IF score có độ phân tán nhất định, không bị collapse về một giá trị.

Diễn giải:

> IF score có spread đủ để dùng làm detector độc lập. Tuy nhiên IF không quyết định một mình; pipeline dùng GMM ∧ IF để giảm false-positive.

### `if_actual_contamination_pct`

Tỷ lệ dòng bị Isolation Forest flag theo từng site.

Config hiện tại:

```text
IF_CONTAMINATION = 0.03
```

Kết quả hiện tại:

```text
khoảng 3.00% trên tất cả site
```

Đây là kết quả tốt, vì IF đang hoạt động đúng theo contamination budget đã cấu hình.

Câu trả lời nếu bị hỏi:

> Isolation Forest được cấu hình contamination 3% trên daytime rows. Kết quả thực tế quanh 3% cho từng site, chứng minh model chạy đúng cơ chế và không bị lệch do night-time zeros.

### `gmm_if_agreement_jaccard_pct`

Mức độ đồng thuận giữa GMM và Isolation Forest.

Công thức:

```text
Jaccard = |GMM flags ∩ IF flags| / |GMM flags ∪ IF flags|
```

Kết quả hiện tại:

```text
khoảng 6.4%–16.7%
```

Diễn giải:

Hai detector không bắt trùng quá nhiều. Điều này là bình thường vì:

- GMM nhìn theo phân phối cục bộ trong từng segment.
- IF nhìn đa biến/toàn cục trên site.

Pipeline chỉ lấy điểm được cả hai đồng thuận trong bước `GMM ∧ IF`, nên Jaccard thấp cho thấy fusion đang lọc mạnh các candidate riêng lẻ.

Câu trả lời nếu bị hỏi:

> GMM và IF là hai detector độc lập. Mức Jaccard 6–17% cho thấy chúng không trùng lặp máy móc. Pipeline lấy phần giao để tăng độ chắc chắn và giảm false-positive.

## 4. Cách trình bày ngắn trong báo cáo

Có thể viết:

```text
Do dữ liệu không có nhãn outlier thủ công, nhóm không đánh giá bằng accuracy/precision/recall. Thay vào đó, nhóm dùng các chỉ số kiểm tra độ ổn định của mô hình không giám sát. Kết quả cho thấy GMM hội tụ 100% trên toàn bộ site, Isolation Forest giữ đúng contamination khoảng 3%, Decision Tree tạo 19–29 segment/site, và GMM-IF agreement Jaccard ở mức 6–17%. Điều này cho thấy pipeline không flag outlier một cách tùy tiện mà sử dụng cơ chế phân đoạn, fit phân phối cục bộ và đồng thuận giữa hai detector độc lập.
```

## 5. Cách trả lời nếu hội đồng hỏi “làm sao biết thuật toán tốt?”

Trả lời:

```text
Vì bài toán không có nhãn outlier thủ công, em không khẳng định bằng accuracy hay F1. Em đánh giá theo hướng unsupervised validation:

1. Kiểm tra phân đoạn: Decision Tree tạo 19–29 segment/site và có R² energy trung bình khoảng 0.76, nghĩa là segment giải thích được profile sản lượng PV.
2. Kiểm tra GMM: tất cả GMM trong các segment hội tụ 100%, đồng thời lưu log-likelihood, BIC và AIC để audit chất lượng fit.
3. Kiểm tra IF: Isolation Forest giữ đúng contamination khoảng 3% trên từng site, không bị night-time zeros làm lệch.
4. Kiểm tra fusion: GMM và IF chỉ đồng thuận khoảng 6–17%, nên final flag là tập đã được lọc qua hai detector độc lập, không phải lấy tất cả candidate thô.

Vì vậy em xem đây là một pipeline phát hiện outlier có cơ sở kỹ thuật và có log audit, không phải rule hardcode tùy ý.
```

## 6. Cần tránh nói gì?

Không nên nói:

```text
Mô hình đạt accuracy X%.
Mô hình có precision/recall tốt.
GMM-IF chắc chắn bắt đúng toàn bộ outlier.
Site nào có BIC thấp hơn thì chắc chắn tốt hơn site khác.
```

Nên nói:

```text
Đây là unsupervised outlier detection nên đánh giá bằng stability metrics, fit-quality metrics và audit trực quan.
Các điểm outlier cuối cùng cần được xem là candidate đáng nghi để BI/ML hoặc domain expert review tiếp.
```

## 7. Những con số nên đưa vào slide

Không đưa bảng 42 dòng vào slide chính. Chỉ đưa:

```text
GMM convergence: 100%
IF actual contamination: ~3%
Decision Tree leaf segments/site: 19–29
Energy R² mean của segmentation: ~0.758
GMM-IF Jaccard agreement: 6.4%–16.7%
Final outlier rate: ~0.47% daytime rows
```

Các bảng chi tiết để trong appendix/log:

```text
reports/gmm_if_report/12_gmm_if_fit_quality_by_site.csv
reports/gmm_if_report/13_gmm_if_fit_quality_summary.log
reports/gmm_if_report/08_decision_tree_segment_r2_summary.log
reports/gmm_if_report/11_gmm_if_model_metrics.log
```
