# Kết nối Supabase — Database & Storage

Hướng dẫn này áp dụng cho **môi trường production (Supabase)**.  
Môi trường local dùng MinIO + Docker Compose (xem `docker-compose.yaml`).

---

## 1. Cấu hình file `.env`

Sao chép `.env.example` thành `.env` rồi điền thông tin thật:

```bash
cp .env.example .env
```

```env
# ── Supabase Python Client ──────────────────────────────────────
SUPABASE_URL=https://<project-id>.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>   # giữ bí mật, không commit

# ── Supabase Storage (S3-compatible) ───────────────────────────
SUPABASE_PROJECT_ID=<project-id>
SUPABASE_S3_ACCESS_KEY=<s3-access-key>         # lấy tại Storage → S3 Access Keys
SUPABASE_S3_SECRET_KEY=<s3-secret-key>
SUPABASE_BUCKET=raw-data

# ── Supabase PostgreSQL (Connection Pooler) ─────────────────────
DB_HOST=aws-1-ap-southeast-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres.<project-id>
DB_PASSWORD=<db-password>
```

> **Lưu ý:** File `.env` đã có trong `.gitignore` — không bao giờ commit file này lên git.

---

## 2. Kết nối PostgreSQL bằng `pg8000`

Dùng cho ETL pipeline (`src/etl/pipeline/`). `pg8000` là Pure Python nên chạy ổn trên mọi OS (Windows, Mac, Linux/NixOS).

```python
import os
import pg8000
from dotenv import load_dotenv

load_dotenv()

conn = pg8000.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM dim_solar_site;")
print(cursor.fetchone())

conn.close()
```

> **Tại sao dùng Connection Pooler?**  
> `DB_HOST=aws-1-ap-southeast-1.pooler.supabase.com` là địa chỉ pooler của Supabase — hỗ trợ IPv4 và cho phép nhiều kết nối đồng thời từ các thành viên nhóm mà không bị lỗi "too many connections".

---

## 3. Kết nối Supabase Storage bằng `boto3`

Supabase Storage tương thích S3 API. Dùng `boto3` để upload/download file CSV — không cần tải về máy, đọc thẳng vào pandas.

```python
import io
import os
import boto3
import pandas as pd
from botocore.client import Config
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{os.getenv('SUPABASE_PROJECT_ID')}.supabase.co/storage/v1/s3",
    aws_access_key_id=os.getenv("SUPABASE_S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("SUPABASE_S3_SECRET_KEY"),
    region_name="ap-southeast-1",
    config=Config(signature_version="s3v4"),
)

BUCKET = os.getenv("SUPABASE_BUCKET", "raw-data")
```

### Upload file lên Storage

```python
s3.upload_file("data/raw/solar_gen_bundoora_raw.csv", BUCKET, "solar_gen_bundoora_raw.csv")
```

### Đọc CSV thẳng vào pandas (không cần tải về máy)

```python
obj = s3.get_object(Bucket=BUCKET, Key="solar_gen_bundoora_raw.csv")
df = pd.read_csv(io.BytesIO(obj["Body"].read()))
print(df.shape)
```

### Liệt kê file trong bucket

```python
res = s3.list_objects_v2(Bucket=BUCKET)
files = [obj["Key"] for obj in res.get("Contents", [])]
print(files)
```

> Lấy S3 credentials tại: **Supabase Dashboard → Storage → S3 Access Keys → New access key**

---

## 4. Kết nối Supabase Python Client

Dùng cho các thao tác qua REST API (auth, realtime, đọc/ghi nhẹ).

```python
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# Client thường — áp dụng Row Level Security (RLS)
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

# Client admin — bypass RLS, dùng cho ETL/script nội bộ
admin = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

# Ví dụ: đọc bảng dim_solar_site
rows = client.table("dim_solar_site").select("*").execute()
print(rows.data)
```

---

## 5. Chuyển ETL từ MinIO (local) sang Supabase (production)

Các file ETL hiện đang hardcode thông tin MinIO local. Khi chuyển lên production, sửa phần config như sau:

**Trong `src/etl/pipeline/load_01_dims.py` và `load_02_facts.py`:**

```python
# ── LOCAL (MinIO) ──
S3 = dict(
    endpoint_url="http://localhost:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin",
    ...
)
DB = "host=localhost port=5432 dbname=postgres user=postgres password=postgres"

# ── PRODUCTION (Supabase) ──
import os
from dotenv import load_dotenv
load_dotenv()

S3 = dict(
    endpoint_url=f"https://{os.getenv('SUPABASE_PROJECT_ID')}.supabase.co/storage/v1/s3",
    aws_access_key_id=os.getenv("SUPABASE_S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("SUPABASE_S3_SECRET_KEY"),
    region_name="ap-southeast-1",
    config=Config(signature_version="s3v4"),
)
DB = (
    f"host={os.getenv('DB_HOST')} port={os.getenv('DB_PORT')} "
    f"dbname={os.getenv('DB_NAME')} user={os.getenv('DB_USER')} "
    f"password={os.getenv('DB_PASSWORD')}"
)
```

**Trong `src/etl/upload_dataraw/upload_raw.py`:**

```python
# ── LOCAL (MinIO) ──
ENDPOINT = "http://localhost:9000"
KEY      = "minioadmin"
SECRET   = "minioadmin"

# ── PRODUCTION (Supabase) ──
ENDPOINT = f"https://{os.getenv('SUPABASE_PROJECT_ID')}.supabase.co/storage/v1/s3"
KEY      = os.getenv("SUPABASE_S3_ACCESS_KEY")
SECRET   = os.getenv("SUPABASE_S3_SECRET_KEY")
```

---

## Tóm tắt nhanh

| Mục đích | Thư viện | File tham khảo |
|---|---|---|
| ETL nạp DB | `pg8000` | `src/etl/pipeline/load_01_dims.py` |
| Upload raw CSV | `boto3` | `src/etl/upload_dataraw/upload_raw.py` |
| Đọc CSV từ Storage | `boto3` | `src/database/supabase_storage.py` |
| REST API / Auth | `supabase` | `src/database.py` |
