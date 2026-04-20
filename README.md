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

### 5. Performance Testing dengan Locust

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

### 6. Jalankan Semua Tests

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
- **Performance Tests (Locust):** Load test simulasi pengguna bersamaan
- **CI/CD:** GitHub Actions workflow otomatis
