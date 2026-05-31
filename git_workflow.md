# TASK 2 — Thiết kế Kiến trúc Kho dữ liệu

## Branch
`feature/data-warehouse-design`

## Quy trình làm việc

1. Checkout branch này trước khi bắt đầu:
   ```bash
   git checkout feature/data-warehouse-design
   ```

2. Sau khi hoàn thành, commit và push:
   ```bash
   git add .
   git commit -m "feat: <mô tả thay đổi>"
   git push origin feature/data-warehouse-design
   ```

3. Tạo Pull Request về `main` khi xong task.

## Lưu ý
- Không làm việc trực tiếp trên `main`.
- Mỗi commit nên rõ ràng, tập trung vào một thay đổi.



```

Có thể ghi đè commit của đồng đội.

---

```bash
git clean -fd
```

Xóa toàn bộ file chưa được Git theo dõi.

---

# Workflow Chuẩn Cho Team

```bash
git checkout feature/data-warehouse-design

git pull --rebase origin feature/data-warehouse-design

# code

git add .

git commit -m "feat(...): ..."

git push origin feature/data-warehouse-design
```
 # Trước khi push nhớ pull code mới về 
 # VD: Đang làm việc ở nhánh feature/datawarehouse thì pull nhánh đó về rồi mới code và push lên
Nếu push lỗi:

```bash
git stash push -u

git pull --rebase origin feature/data-warehouse-design

git stash pop

git add .

git commit -m "chore: resolve after rebase"

git push origin feature/data-warehouse-design
```

Đây là workflow an toàn nhất cho đa số dự án sử dụng Git Flow hoặc Feature Branch.
