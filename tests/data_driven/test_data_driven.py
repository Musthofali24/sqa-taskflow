# tests/data_driven/test_data_driven.py
"""
Challenge 3: Data-Driven Testing dengan File JSON
--------------------------------------------------
Cara menjalankan (dari folder taskflow/):
    pytest tests/data_driven/test_data_driven.py -v
"""

import json
from pathlib import Path

import pytest
import requests

# URL API dan lokasi file data
TASKS_URL = "http://127.0.0.1:8000/api/tasks"
DATA_FILE = Path(__file__).parent / "task_test_data.json"


def load_test_cases():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data["test_cases"]


@pytest.mark.parametrize(
    "test_case",
    load_test_cases(),
    ids=[tc["test_id"] for tc in load_test_cases()],
)
def test_create_task_from_json(test_case):
    """
    Kirim POST /api/tasks sesuai payload dari JSON.
    Verifikasi: status code dan field penting di response.
    """
    payload = test_case["payload"]
    expected_status = test_case["expected_status"]
    description = test_case["description"]

    # 1. Kirim request
    response = requests.post(TASKS_URL, json=payload, timeout=10)

    # 2. Cek status code
    assert response.status_code == expected_status, (
        f"[{test_case['test_id']}] {description}\n"
        f"  Expected: {expected_status}, Got: {response.status_code}\n"
        f"  Body: {response.text[:300]}"
    )

    body = response.json()

    # 3. Cek assertions dari JSON
    for key, value in test_case.get("assertions", {}).items():

        if key == "has_id":
            # Response harus punya field 'id' berupa integer
            assert "id" in body and isinstance(body["id"], int)

        elif key == "has_created_at":
            # Response harus punya field 'created_at' yang tidak kosong
            assert body.get("created_at")

        elif key == "has_detail":
            # Response error harus punya field 'detail'
            assert "detail" in body

        elif key == "error_field":
            # Nama field yang salah harus muncul di dalam 'detail[].loc'
            all_locs = [
                str(x) for item in body.get("detail", []) for x in item.get("loc", [])
            ]
            assert (
                value in all_locs
            ), f"Field '{value}' tidak ada di error detail: {all_locs}"

        else:
            assert (
                body.get(key) == value
            ), f"Field '{key}': expected '{value}', got '{body.get(key)}'"

    # Hapus task yang berhasil dibuat agar tidak menumpuk di DB
    if response.status_code == 201:
        requests.delete(f"{TASKS_URL}/{body['id']}", timeout=5)
