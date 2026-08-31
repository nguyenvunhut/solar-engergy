# Notebook 05c — Chọn công thức chuẩn hoá (`05c_thuc_nghiem_mau_so_chuan_hoa.ipynb`)

>  **Về các con số trong file này:** một số giá trị mô tả lượt chạy ngày 19/08 hoặc
> trưa 20/08. Giá trị **hiện hành** và lý do từng con số thay đổi được liệt kê đầy đủ ở
> [`20_GIAI_THICH_SO_MAU_THUAN.md`](20_GIAI_THICH_SO_MAU_THUAN.md). Đọc file đó trước khi
> trích bất kỳ con số nào vào báo cáo.


## Câu hỏi cần trả lời
Mẫu số `site_scale × sin(góc cao)` là **lựa chọn của dự án**. Trong tài liệu có công thức
khác của Lonij và cộng sự (2012). Vậy công thức nào tốt hơn **trên dữ liệu này**?

- **Vào:** `05_selected/v5_{train,val}_selected.parquet`
- **Ra:** `05c_thuc_nghiem_mau_so/thuc_nghiem_mau_so_chuan_hoa.csv` + hình

## Ba họ mẫu số được so
| Ký hiệu | Công thức | Nguồn |
|---|---|---|
| `lonij` | phân vị 80 sản lượng đo được tại **cùng khung giờ**, **15 ngày liền trước** | Lonij 2012 |
| `toan_cuc` | phân vị 99 sản lượng của trạm (cố định) × sin(góc cao) | Dự án |
| `truot_N` | như trên nhưng phân vị tính trên cửa sổ trượt N ngày | Biến thể |

```
CAC_CUA_SO = [7, 15, 30, 60, 90, 180, 365]
```
Tổng cộng **9 phương án**.

## Cách chạy một thí nghiệm cho công bằng
Mọi phương án dùng **cùng bộ đặc trưng, cùng siêu tham số, cùng hạt giống, cùng tập dòng để
chấm**. Chỉ đổi mẫu số. Ngưỡng cắt nhãn của mỗi phương án được suy lại từ phân bố `k` của
**chính phương án đó** trên tập train — vì mỗi mẫu số cho một phân bố `k` khác nhau.

Đây là chỗ dễ hiểu nhầm: ngưỡng cắt của phương án cửa sổ trượt ra ~1,8–1,9 trong khi phương
án toàn cục ra ~1,36. Không mâu thuẫn — **cùng một luật (phân vị 99), con số tự thích nghi
theo mẫu số**.

## Kết quả lần chạy 19/08
| Phương án | WAPE |
|---|---|
| **Biến thể dự án (toàn cục × sin)** | **22,0845%** ← chọn |
| Cửa sổ trượt 30 ngày (tốt nhất nhóm trượt) | 22,5355% |
| Lonij (2012) nguyên bản | 25,1552% |

Dự án thắng công thức của bài báo **3,07 điểm** — khoảng cách này lớn gấp ~50 lần độ lệch
chuẩn nhiễu (0,06), nên là khác biệt thật, không phải may mắn.

## Cổng kiểm chứng tái lập
Chạy lại phương án thắng cuộc lần thứ hai và so từng phần tử của vector dự báo. Kết quả:
ngưỡng cắt khớp tới 10 chữ số, WAPE khớp tới 10 chữ số, **vector dự báo giống hệt từng phần
tử**. Điều này chứng minh mọi khác biệt giữa các phương án là do phương án, không do ngẫu
nhiên.
