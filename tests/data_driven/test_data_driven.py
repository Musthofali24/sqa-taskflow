# tests/data_driven/test_data_driven.py
"""
Challenge 3: Data-Driven Testing dengan File JSON
================================================
Script ini membaca test case dari task_test_data.json dan menjalankan
setiap kasus uji secara otomatis terhadap TaskFlow API menggunakan
library `requests` dan `pytest`.

Cara menjalankan (dari folder taskflow/):
    pytest tests/data_driven/test_data_driven.py -v
    pytest tests/data_driven/test_data_driven.py -v --html=reports/data-driven-report.html --self-contained-html
"""

import json
import os
import time
from pathlib import Path
from typing import Any

import pytest
import requests

# ========== Konfigurasi ==========
BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
TASKS_URL = f"{BASE_URL}/api/tasks"
DATA_FILE = Path(__file__).parent / "task_test_data.json"


# ========== Helper: Muat data dari JSON ==========
def load_test_data() -> list[dict]:
    """Membaca file JSON dan mengembalikan list test cases."""
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data["test_cases"]


def pytest_generate_tests(metafunc):
    """
    Hook pytest untuk generate parameter test secara dinamis dari JSON.
    Digunakan oleh semua test function yang memiliki fixture 'test_case'.
    """
    if "test_case" in metafunc.fixturenames:
        test_cases = load_test_data()
        ids = [f"{tc['test_id']} - {tc['description']}" for tc in test_cases]
        metafunc.parametrize("test_case", test_cases, ids=ids)


# ========== Fixture ==========
@pytest.fixture(scope="module")
def api_available():
    """Pastikan API server berjalan sebelum menjalankan tests."""
    try:
        resp = requests.get(BASE_URL, timeout=5)
        assert resp.status_code == 200, f"API tidak bisa diakses: {resp.status_code}"
    except requests.ConnectionError:
        pytest.skip(
            f"API server tidak berjalan di {BASE_URL}. Jalankan backend terlebih dahulu."
        )


@pytest.fixture(autouse=True)
def _require_api(api_available):
    """Dependensi implisit ke api_available untuk semua test."""
    pass


# ========== Helper: Bersihkan task yang dibuat ==========
created_task_ids: list[int] = []


@pytest.fixture(scope="module", autouse=True)
def cleanup_created_tasks():
    """Hapus semua task yang dibuat selama test suite berjalan (teardown)."""
    yield
    for task_id in created_task_ids:
        try:
            requests.delete(f"{TASKS_URL}/{task_id}", timeout=5)
        except Exception:
            pass
    created_task_ids.clear()


# ========== Helper Functions ==========
def post_task(payload: dict) -> requests.Response:
    """Kirim POST request ke /api/tasks."""
    return requests.post(TASKS_URL, json=payload, timeout=10)


def assert_response_status(response: requests.Response, expected: int, test_id: str):
    """Verifikasi HTTP status code."""
    assert response.status_code == expected, (
        f"[{test_id}] Expected status {expected}, got {response.status_code}. "
        f"Body: {response.text[:300]}"
    )


def assert_response_assertions(
    response_json: dict | list,
    assertions: dict,
    test_id: str,
):
    """Verifikasi properti respons sesuai assertions dari JSON."""
    for key, expected_value in assertions.items():
        if key == "has_id":
            assert "id" in response_json and isinstance(
                response_json["id"], int
            ), f"[{test_id}] Response harus memiliki field 'id' bertipe integer"

        elif key == "has_created_at":
            assert (
                "created_at" in response_json and response_json["created_at"]
            ), f"[{test_id}] Response harus memiliki field 'created_at' yang terisi"

        elif key == "has_detail":
            assert (
                "detail" in response_json
            ), f"[{test_id}] Response error harus memiliki field 'detail'"

        elif key == "error_field":
            # Cari nama field di seluruh struktur 'detail'
            detail = response_json.get("detail", [])
            all_locs: list[str] = []
            for item in detail:
                loc = item.get("loc", [])
                all_locs.extend([str(x) for x in loc])
            assert expected_value in all_locs, (
                f"[{test_id}] Field '{expected_value}' tidak ditemukan dalam error detail. "
                f"Locs yang tersedia: {all_locs}"
            )

        else:
            # Pengecekan nilai langsung
            assert (
                key in response_json
            ), f"[{test_id}] Field '{key}' tidak ada dalam respons"
            assert response_json[key] == expected_value, (
                f"[{test_id}] Field '{key}': expected '{expected_value}', "
                f"got '{response_json[key]}'"
            )


# ========== Main Test: Parametrized dari JSON ==========
class TestDataDriven:
    """
    Suite test data-driven yang membaca setiap test case dari task_test_data.json
    dan memvalidasi respons API sesuai expected_status dan assertions.
    """

    def test_create_task_from_json(self, test_case: dict):
        """
        TC generik: buat tugas sesuai payload dari JSON, verifikasi status dan assertions.
        Dijalankan sekali per setiap test case yang ada di task_test_data.json.
        """
        test_id = test_case["test_id"]
        payload = test_case["payload"]
        expected_status = test_case["expected_status"]
        assertions = test_case.get("assertions", {})

        # Act
        response = post_task(payload)

        # Assert: HTTP status code
        assert_response_status(response, expected_status, test_id)

        # Assert: struktur dan nilai respons
        response_json = response.json()
        assert_response_assertions(response_json, assertions, test_id)

        # Simpan ID jika task berhasil dibuat agar bisa dibersihkan nanti
        if expected_status == 201 and "id" in response_json:
            created_task_ids.append(response_json["id"])


# ========== Test Tambahan: Validasi Struktur JSON data file ==========
class TestDataFileStructure:
    """Validasi bahwa file JSON test data memiliki struktur yang benar."""

    def test_data_file_exists(self):
        """File task_test_data.json harus ada."""
        assert DATA_FILE.exists(), f"File tidak ditemukan: {DATA_FILE}"

    def test_data_file_is_valid_json(self):
        """File harus valid JSON."""
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        assert "test_cases" in data, "Key 'test_cases' tidak ada di file JSON"

    def test_minimum_10_test_cases(self):
        """Minimal 10 test case harus tersedia."""
        cases = load_test_data()
        assert (
            len(cases) >= 10
        ), f"Hanya ada {len(cases)} test case, minimal 10 diperlukan"

    def test_each_case_has_required_keys(self):
        """Setiap test case harus memiliki field wajib."""
        required_keys = {
            "test_id",
            "description",
            "payload",
            "expected_status",
            "assertions",
        }
        cases = load_test_data()
        for case in cases:
            missing = required_keys - set(case.keys())
            assert (
                not missing
            ), f"Test case '{case.get('test_id', '?')}' kekurangan field: {missing}"

    def test_has_both_valid_and_invalid_cases(self):
        """Harus ada kasus valid (201) dan invalid (422)."""
        cases = load_test_data()
        valid_cases = [c for c in cases if c["expected_status"] == 201]
        invalid_cases = [c for c in cases if c["expected_status"] == 422]
        assert len(valid_cases) >= 1, "Tidak ada kasus valid (expected_status=201)"
        assert len(invalid_cases) >= 1, "Tidak ada kasus invalid (expected_status=422)"

    def test_all_test_ids_are_unique(self):
        """Semua test_id harus unik."""
        cases = load_test_data()
        ids = [c["test_id"] for c in cases]
        assert len(ids) == len(set(ids)), f"Ada test_id yang duplikat: {ids}"


# ========== Test Tambahan: Filter & Pencarian ==========
class TestFilterAndSearch:
    """Verifikasi endpoint GET /api/tasks dengan query params filter dan search."""

    @pytest.fixture(autouse=True)
    def seed_tasks(self):
        """Buat beberapa task sebagai data fixture untuk test filter/search."""
        self._created = []

        seed_data = [
            {
                "title": "DD Filter Pending Alpha",
                "status": "pending",
                "priority": "high",
            },
            {"title": "DD Filter Pending Beta", "status": "pending", "priority": "low"},
            {
                "title": "DD Filter Completed Gamma",
                "status": "completed",
                "priority": "medium",
            },
            {
                "title": "DD Search Khusus Keyword",
                "description": "ini mengandung keyword unik: DDTEST123",
                "status": "in-progress",
                "priority": "medium",
            },
        ]

        for item in seed_data:
            resp = post_task(item)
            if resp.status_code == 201:
                self._created.append(resp.json()["id"])
                created_task_ids.append(resp.json()["id"])

        yield

    def test_filter_by_status_pending_only(self):
        """GET /api/tasks?status=pending hanya boleh mengembalikan task pending."""
        resp = requests.get(TASKS_URL, params={"status": "pending"}, timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        for task in data:
            assert (
                task["status"] == "pending"
            ), f"Task id={task['id']} berstatus '{task['status']}', bukan 'pending'"

    def test_filter_by_status_completed_only(self):
        """GET /api/tasks?status=completed hanya boleh mengembalikan task completed."""
        resp = requests.get(TASKS_URL, params={"status": "completed"}, timeout=10)
        assert resp.status_code == 200
        for task in resp.json():
            assert task["status"] == "completed"

    def test_search_by_keyword_in_title(self):
        """GET /api/tasks?search=DD Filter harus mengembalikan task yang mengandung keyword di judul."""
        resp = requests.get(TASKS_URL, params={"search": "DD Filter"}, timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1, "Pencarian 'DD Filter' harus menemukan minimal 1 task"
        for task in data:
            title_match = "DD Filter" in task.get("title", "")
            desc_match = "DD Filter" in (task.get("description") or "")
            assert (
                title_match or desc_match
            ), f"Task id={task['id']} tidak mengandung keyword 'DD Filter'"

    def test_search_by_keyword_in_description(self):
        """GET /api/tasks?search=DDTEST123 harus menemukan task yang keywordnya ada di description."""
        resp = requests.get(TASKS_URL, params={"search": "DDTEST123"}, timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1, "Pencarian 'DDTEST123' harus menemukan minimal 1 task"
        for task in data:
            title_match = "DDTEST123" in task.get("title", "")
            desc_match = "DDTEST123" in (task.get("description") or "")
            assert title_match or desc_match

    def test_search_no_match_returns_empty_list(self):
        """GET /api/tasks?search=NOTEXIST999 harus mengembalikan array kosong."""
        resp = requests.get(
            TASKS_URL, params={"search": "NOTEXIST_XXXXXXXXXXX"}, timeout=10
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_combined_status_and_search_filter(self):
        """GET /api/tasks?status=pending&search=Alpha harus mengembalikan hanya task pending yang mengandung 'Alpha'."""
        resp = requests.get(
            TASKS_URL, params={"status": "pending", "search": "Alpha"}, timeout=10
        )
        assert resp.status_code == 200
        data = resp.json()
        for task in data:
            assert task["status"] == "pending"
            title_match = "Alpha" in task.get("title", "")
            desc_match = "Alpha" in (task.get("description") or "")
            assert title_match or desc_match


# ========== Test Tambahan: CRUD Lengkap ==========
class TestCRUDOperations:
    """Verifikasi operasi GET single, PUT, dan DELETE setelah POST."""

    def test_get_task_by_id_after_create(self):
        """Setelah membuat task, GET /api/tasks/{id} harus mengembalikan data yang sama."""
        payload = {
            "title": "GET Single Test DD",
            "status": "pending",
            "priority": "low",
        }
        create_resp = post_task(payload)
        assert create_resp.status_code == 201
        task_id = create_resp.json()["id"]
        created_task_ids.append(task_id)

        get_resp = requests.get(f"{TASKS_URL}/{task_id}", timeout=10)
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["id"] == task_id
        assert data["title"] == payload["title"]
        assert data["status"] == payload["status"]

    def test_update_task_changes_fields(self):
        """PUT /api/tasks/{id} harus mengubah field yang dikirim."""
        payload = {"title": "Update Test DD", "status": "pending", "priority": "low"}
        create_resp = post_task(payload)
        assert create_resp.status_code == 201
        task_id = create_resp.json()["id"]
        created_task_ids.append(task_id)

        update_payload = {
            "title": "Update Test DD - Revised",
            "status": "completed",
            "priority": "high",
        }
        put_resp = requests.put(
            f"{TASKS_URL}/{task_id}", json=update_payload, timeout=10
        )
        assert put_resp.status_code == 200
        updated = put_resp.json()
        assert updated["title"] == update_payload["title"]
        assert updated["status"] == "completed"
        assert updated["priority"] == "high"
        assert updated["updated_at"] is not None

    def test_delete_task_returns_204(self):
        """DELETE /api/tasks/{id} harus mengembalikan 204 No Content."""
        payload = {"title": "Delete Test DD", "status": "pending", "priority": "medium"}
        create_resp = post_task(payload)
        assert create_resp.status_code == 201
        task_id = create_resp.json()["id"]

        del_resp = requests.delete(f"{TASKS_URL}/{task_id}", timeout=10)
        assert del_resp.status_code == 204

        # Pastikan task benar-benar hilang
        get_resp = requests.get(f"{TASKS_URL}/{task_id}", timeout=10)
        assert get_resp.status_code == 404

    def test_get_nonexistent_task_returns_404(self):
        """GET /api/tasks/99999 harus mengembalikan 404."""
        resp = requests.get(f"{TASKS_URL}/99999999", timeout=10)
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Tugas tidak ditemukan"
