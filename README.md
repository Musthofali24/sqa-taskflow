## Cara Menjalankan

### 1. Setup Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Buka: http://127.0.0.1:8000/docs untuk Swagger UI

### 2. Setup Frontend

```bash
cd frontend
php -S 127.0.0.1:8080
```

Buka: http://127.0.0.1:8080

### 3. API Testing dengan Newman

```bash
# Install Newman (satu kali saja)
npm install -g newman newman-reporter-htmlextra
```

```bash
# Pastikan berada di folder taskflow/
cd taskflow

# Jalankan tests (CLI output saja)
npx newman run tests/postman/TaskFlow_API_Collection.json \
    -e tests/postman/TaskFlow_Local_Environment.json

# Jalankan tests + generate HTML report
mkdir -p reports
npx newman run tests/postman/TaskFlow_API_Collection.json \
    -e tests/postman/TaskFlow_Local_Environment.json \
    -r htmlextra --reporter-htmlextra-export reports/api-report.html
```

Report tersimpan di: `reports/api-report.html`

### 4. UI Testing dengan Selenium

```bash
pip install selenium pytest pytest-html webdriver-manager requests

cd tests/selenium
pytest test_frontend.py -v --html=../../reports/frontend-report.html --self-contained-html
```

### 5. Data-Driven Testing (Challenge 3)

Test API otomatis berbasis file JSON. Setiap baris di `task_test_data.json` menjadi satu skenario uji.

```bash
# Dari folder taskflow/
pytest tests/data_driven/test_data_driven.py -v

# Dengan HTML report
pytest tests/data_driven/test_data_driven.py -v \
    --html=reports/data-driven-report.html --self-contained-html
```

**Struktur `tests/data_driven/task_test_data.json`:**

Setiap objek dalam array `test_cases` memiliki field:

| Field             | Tipe    | Keterangan                                             |
| ----------------- | ------- | ------------------------------------------------------ |
| `test_id`         | string  | ID unik, misal `TC-DD-001`                             |
| `description`     | string  | Deskripsi skenario                                     |
| `category`        | string  | `valid`, `invalid_field`, `invalid_value`, `edge_case` |
| `payload`         | object  | Body JSON yang dikirim ke `POST /api/tasks`            |
| `expected_status` | integer | HTTP status code yang diharapkan (`201` atau `422`)    |
| `assertions`      | object  | Properti dan nilai yang harus ada/cocok di respons     |

**Kunci assertions yang didukung:**

| Kunci            | Perilaku                                                |
| ---------------- | ------------------------------------------------------- |
| `has_id`         | Memastikan field `id` bertipe integer ada di respons    |
| `has_created_at` | Memastikan field `created_at` terisi                    |
| `has_detail`     | Memastikan field `detail` ada (untuk error 422)         |
| `error_field`    | Memastikan nama field tersebut muncul di `detail[].loc` |
| field lainnya    | Pengecekan nilai langsung, misal `"status": "pending"`  |

**Distribusi 15 test case:**

| Kategori        | Jumlah | Contoh                                          |
| --------------- | ------ | ----------------------------------------------- |
| `valid`         | 6      | Field lengkap, hanya title, deskripsi panjang   |
| `edge_case`     | 3      | Judul sangat panjang, karakter spesial, unicode |
| `invalid_field` | 3      | Tanpa title, title null, payload kosong         |
| `invalid_value` | 3      | Status salah, priority salah, keduanya salah    |

### 6. Performance Testing dengan Locust

```bash
pip install locust

# Web UI (buka http://localhost:8089)
locust -f tests/performance/locustfile.py --host=http://127.0.0.1:8000

# Headless
locust -f tests/performance/locustfile.py \
    --host=http://127.0.0.1:8000 \
    --headless --users 50 --spawn-rate 5 --run-time 60s \
    --html=reports/performance-report.html
```

### 7. Jalankan Semua Tests

```bash
python run_all_tests.py
```

## API Endpoints

| Method | Endpoint                                 | Deskripsi                        |
| ------ | ---------------------------------------- | -------------------------------- |
| GET    | /                                        | Welcome message                  |
| POST   | /api/tasks                               | Buat tugas baru                  |
| GET    | /api/tasks                               | Daftar semua tugas               |
| GET    | /api/tasks?status=pending                | Filter berdasarkan status        |
| GET    | /api/tasks?search=keyword                | Cari berdasarkan judul/deskripsi |
| GET    | /api/tasks?status=pending&search=keyword | Kombinasi filter & pencarian     |
| GET    | /api/tasks/{id}                          | Detail satu tugas                |
| PUT    | /api/tasks/{id}                          | Update tugas                     |
| DELETE | /api/tasks/{id}                          | Hapus tugas                      |

### Field Tugas

| Field       | Tipe   | Nilai yang diizinkan                  |
| ----------- | ------ | ------------------------------------- |
| title       | string | wajib diisi                           |
| description | string | opsional                              |
| status      | string | `pending`, `in-progress`, `completed` |
| priority    | string | `low`, `medium` (default), `high`     |

## Test Coverage

- **API Tests (Postman/Newman):** 11 test cases — CRUD, validasi, filter status, pencarian keyword, kombinasi filter+search, empty result
- **UI Tests (Selenium):** 16 test cases — CRUD, modal, badge, filter status, pencarian keyword, empty search result, clear search
- **Data-Driven Tests (pytest + JSON):** 31 test — 15 skenario parametrized dari JSON, 6 validasi file data, 6 filter & search, 4 CRUD lifecycle
- **Performance Tests (Locust):** Load test simulasi pengguna bersamaan
- **CI/CD:** GitHub Actions workflow otomatis
