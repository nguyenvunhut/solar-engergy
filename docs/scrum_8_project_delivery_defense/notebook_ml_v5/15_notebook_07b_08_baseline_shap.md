# Notebook 07b và 08 — Đối chứng và giải thích

> **Về các con số trong file này:** một số giá trị mô tả lượt chạy ngày 19/08 hoặc
> trưa 20/08. Giá trị **hiện hành** và lý do từng con số thay đổi được liệt kê đầy đủ ở
> [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md). Đọc file đó trước khi
> trích bất kỳ con số nào vào báo cáo.


## 07b — So với Prophet (`07b_baseline_prophet.ipynb`)

### Nhiệm vụ
Trả lời câu *"mô hình phức tạp của các em có hơn một phương pháp đơn giản không?"*

Prophet là thư viện dự báo chuỗi thời gian của Meta, phân rã chuỗi thành xu hướng + chu kỳ.
Nó **không dùng thời tiết**, chỉ dùng thời gian.

### Phép tính bằng tay
```
Skill Score = (1 − WAPE_mô_hình / WAPE_đối_chứng) × 100
```
Dương nghĩa là tốt hơn đối chứng. Kết quả lần chạy 19/08: h1 **+48,73%**, h4 **+35,89%**.

Điều kiện bắt buộc: **cùng tập dòng** cho cả hai mô hình, và Prophet đọc tham số chuẩn hoá
từ chính `model_config.json` của LightGBM để hai bên nhân ngược giống nhau.

### Một đối chứng khác quan trọng hơn: persistence
"Persistence" nghĩa là **chép giá trị gần nhất** làm dự báo. Với dự báo mặt trời tầm rất
ngắn, đây là đối chứng khó vượt và là chuẩn trong ngành. Số đo trên tập kiểm định 19/08:
persistence 20,46% so với mô hình 22,29% ở h1 — **mô hình thua ở tầm 15 phút**. Điều này cần
nêu thẳng trong báo cáo, kèm giải thích: ở tầm 15 phút, trạng thái trời gần như không đổi nên
quán tính rất mạnh; giá trị của mô hình nằm ở tầm dài hơn.

## 08 — Giải thích bằng SHAP (`08_explainable_ai.ipynb`)

### Nhiệm vụ
Mở "hộp đen": chỉ ra từng đặc trưng đẩy dự báo lên hay xuống bao nhiêu.

### Phép tính bằng tay
SHAP xuất phát từ lý thuyết trò chơi hợp tác: coi mỗi đặc trưng là một "người chơi" và chia
phần đóng góp vào kết quả một cách công bằng. Notebook dùng
`booster_.predict(pred_contrib=True)` — chính là cài đặt TreeSHAP của Lundberg trong lõi C++
của LightGBM, cho ra **cùng giá trị** với thư viện `shap` nhưng nhanh hơn nhiều bậc.

```
Tầm quan trọng toàn cục = trung bình |giá trị SHAP| trên toàn bộ dòng
```

Ba loại biểu đồ:
- **Beeswarm**: toàn cảnh — mỗi chấm là một dòng dữ liệu.
- **Dependence**: một đặc trưng thay đổi thì ảnh hưởng đổi ra sao.
- **Waterfall**: giải thích **một** dự báo cụ thể, từng bước một.

### Lưu ý kỹ thuật
Bảng xếp hạng tính trên **toàn bộ** dòng của tập test; riêng hình beeswarm vẽ trên mẫu ngẫu
nhiên 20.000 dòng vì vẽ 475.000 chấm sẽ treo trình vẽ. Điều này được ghi rõ trong notebook để
không ai hiểu nhầm là bảng xếp hạng cũng chỉ dựa trên mẫu.
