# tests/performance/locustfile.py
from locust import HttpUser, task, between


class TaskFlowUser(HttpUser):
    """Simulasi pengguna TaskFlow"""

    wait_time = between(1, 3)  # Waktu tunggu antar task (1-3 detik)

    def on_start(self):
        """Dijalankan saat user mulai"""
        self.task_ids = []

    @task(3)  # Weight = 3 (lebih sering dijalankan)
    def view_all_tasks(self):
        """Melihat daftar semua tugas"""
        with self.client.get("/api/tasks", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")

    @task(2)
    def create_task(self):
        """Membuat tugas baru"""
        task_data = {
            "title": f"Load Test Task {self.environment.runner.user_count}",
            "description": "Created during load testing",
            "status": "pending",
        }

        with self.client.post(
            "/api/tasks", json=task_data, catch_response=True
        ) as response:
            if response.status_code == 201:
                task_id = response.json().get("id")
                if task_id:
                    self.task_ids.append(task_id)
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")

    @task(1)
    def update_task(self):
        """Memperbarui tugas yang ada"""
        if not self.task_ids:
            # Ambil task ID dari API jika belum ada
            response = self.client.get("/api/tasks")
            if response.status_code == 200 and response.json():
                self.task_ids = [task["id"] for task in response.json()]

        if self.task_ids:
            task_id = self.task_ids[0]
            update_data = {
                "title": f"Updated Task {task_id}",
                "description": "Updated during load test",
                "status": "in-progress",
            }

            with self.client.put(
                f"/api/tasks/{task_id}", json=update_data, catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Failed: {response.status_code}")

    @task(1)
    def delete_task(self):
        """Menghapus tugas"""
        if self.task_ids:
            task_id = self.task_ids.pop()
            with self.client.delete(
                f"/api/tasks/{task_id}", catch_response=True
            ) as response:
                if response.status_code == 204:
                    response.success()
                else:
                    response.failure(f"Failed: {response.status_code}")

    def on_stop(self):
        """Dijalankan saat user berhenti - cleanup"""
        for task_id in self.task_ids:
            self.client.delete(f"/api/tasks/{task_id}")
