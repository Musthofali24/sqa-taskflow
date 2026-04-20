# tests/selenium/test_frontend.py
import pytest
import time
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.task_page import TaskPage

API_URL = "http://127.0.0.1:8000/api/tasks"


class TestTaskFlowFrontend:
    """Test suite untuk frontend TaskFlow"""

    @pytest.fixture(autouse=True)
    def setup(self, driver):
        """Setup sebelum setiap test"""
        self.page = TaskPage(driver)
        self.driver = driver
        # Refresh halaman untuk memastikan state bersih
        self.page.refresh_tasks()

    # ========== Test Cases ==========

    def test_page_loads_correctly(self):
        """TC-FE-001: Memastikan halaman dapat dimuat dengan benar"""
        assert "TaskFlow" in self.driver.title
        assert self.driver.find_element(*self.page.FORM_TITLE) is not None
        print("✓ Halaman berhasil dimuat")

    def test_create_new_task_success(self):
        """TC-FE-002: Membuat tugas baru dengan data valid"""
        # Arrange
        task_title = f"Test Task {time.time()}"
        task_desc = "Ini adalah tugas test"
        task_status = "pending"

        # Act
        self.page.create_task(task_title, task_desc, task_status)

        # Assert
        assert self.page.task_exists(task_title), "Tugas tidak muncul di tabel"
        alert_msg = self.page.get_alert_message()
        assert "berhasil ditambahkan" in alert_msg
        print(f"✓ Tugas '{task_title}' berhasil dibuat")

    def test_create_task_without_title_validation(self):
        """TC-FE-003: Validasi client-side untuk field judul kosong"""
        # Act - Submit form tanpa mengisi judul
        self.driver.find_element(*self.page.BTN_SUBMIT).click()

        # Assert - Cek validasi HTML5 required
        title_input = self.driver.find_element(*self.page.FORM_TITLE)
        validation_message = self.driver.execute_script(
            "return arguments[0].validationMessage;", title_input
        )
        assert len(validation_message) > 0, "Validasi tidak muncul untuk field kosong"
        print("✓ Validasi judul kosong berfungsi")

    def test_reset_form_functionality(self):
        """TC-FE-004: Memastikan tombol reset mengosongkan form"""
        # Arrange - Isi form dulu
        self.driver.find_element(*self.page.FORM_TITLE).send_keys("Test Reset")
        self.driver.find_element(*self.page.FORM_DESCRIPTION).send_keys(
            "Deskripsi test"
        )

        # Act
        self.page.reset_form()

        # Assert
        form_values = self.page.get_form_values()
        assert form_values["title"] == "", "Judul tidak tereset"
        assert form_values["description"] == "", "Deskripsi tidak tereset"
        print("✓ Form reset berfungsi")

    def test_edit_task_functionality(self):
        """TC-FE-005: Mengedit tugas yang sudah ada"""
        # Arrange - Buat tugas dulu
        original_title = f"Edit Test {time.time()}"
        self.page.create_task(original_title, "Deskripsi awal", "pending")

        # Act - Edit tugas
        self.page.click_edit_task(original_title)
        new_title = f"{original_title} (Updated)"
        self.page.update_task_in_modal(
            title=new_title, description="Deskripsi setelah update", status="completed"
        )

        # Assert
        assert self.page.task_exists(
            new_title
        ), "Tugas dengan judul baru tidak ditemukan"
        assert not self.page.task_exists(original_title), "Tugas lama masih ada"

        task = self.page.get_task_by_title(new_title)
        assert task["status"] == "Completed"
        print(f"✓ Tugas berhasil diedit menjadi '{new_title}'")

    def test_delete_task_functionality(self):
        """TC-FE-006: Menghapus tugas"""
        # Arrange
        task_title = f"Delete Test {time.time()}"
        self.page.create_task(task_title, "Akan dihapus", "pending")
        assert self.page.task_exists(task_title), "Tugas tidak berhasil dibuat"

        # Act
        self.page.click_delete_task(task_title)
        self.page.handle_delete_confirmation(accept=True)

        # Assert - Tunggu alert sukses
        alert_msg = self.page.get_alert_message()
        assert "berhasil dihapus" in alert_msg.lower()
        assert not self.page.task_exists(task_title), "Tugas masih ada setelah dihapus"
        print(f"✓ Tugas '{task_title}' berhasil dihapus")

    def test_delete_task_cancelled(self):
        """TC-FE-007: Membatalkan penghapusan tugas"""
        # Arrange
        task_title = f"Cancel Delete {time.time()}"
        self.page.create_task(task_title, "Tidak jadi dihapus", "pending")

        # Act
        self.page.click_delete_task(task_title)
        self.page.handle_delete_confirmation(accept=False)

        # Assert
        time.sleep(0.5)  # Tunggu dialog tertutup
        assert self.page.task_exists(
            task_title
        ), "Tugas hilang padahal delete dibatalkan"
        print("✓ Pembatalan delete berfungsi")

    def test_refresh_button(self):
        """TC-FE-008: Memastikan tombol refresh memuat ulang data"""
        # Arrange - Buat tugas baru via API langsung (simulasi perubahan dari luar)
        unique_title = f"API Created Task {time.time()}"
        new_task = {
            "title": unique_title,
            "description": "Dibuat via API",
            "status": "pending",
        }
        response = requests.post(API_URL, json=new_task)
        assert response.status_code == 201

        # Act - Klik refresh
        self.page.refresh_tasks()

        # Assert
        assert self.page.task_exists(
            unique_title
        ), "Tugas dari API tidak muncul setelah refresh"
        print("✓ Tombol refresh berfungsi")

    def test_status_badge_colors(self):
        """TC-FE-009: Memastikan status badge ditampilkan dengan warna yang benar"""
        # Arrange - Buat tugas dengan berbagai status
        tasks_data = [
            (f"Task Pending {time.time()}", "pending", "bg-warning"),
            (f"Task Progress {time.time()}", "in-progress", "bg-info"),
            (f"Task Completed {time.time()}", "completed", "bg-success"),
        ]

        for title, status, expected_class in tasks_data:
            self.page.create_task(title, f"Test {status}", status)
            self.page.wait_for_alert_to_disappear()

        # Assert - Cek badge classes
        rows = self.driver.find_elements(*self.page.TASKS_TABLE_ROWS)
        badge_map = {}
        for row in rows:
            row_text = row.text
            try:
                badge = row.find_element(By.CSS_SELECTOR, ".badge")
                badge_class = badge.get_attribute("class")
                badge_map[row_text] = badge_class
            except Exception:
                pass

        for title, _, expected_class in tasks_data:
            found = any(
                expected_class in cls for key, cls in badge_map.items() if title in key
            )
            assert (
                found
            ), f"Badge dengan class '{expected_class}' tidak ditemukan untuk '{title}'"

        print("✓ Status badge ditampilkan dengan benar")

    def test_modal_close_with_cancel_button(self):
        """TC-FE-010: Memastikan modal edit bisa ditutup dengan tombol Batal"""
        # Arrange
        task_title = f"Modal Test {time.time()}"
        self.page.create_task(task_title, "Test modal", "pending")

        # Test: Tutup dengan tombol Batal
        self.page.click_edit_task(task_title)
        self.driver.find_element(*self.page.BTN_CANCEL_EDIT).click()

        wait = WebDriverWait(self.driver, 5)
        wait.until(EC.invisibility_of_element_located(self.page.MODAL_EDIT))

        modal = self.driver.find_element(*self.page.MODAL_EDIT)
        assert not modal.is_displayed(), "Modal masih tampil setelah klik Batal"
        print("✓ Modal bisa ditutup dengan tombol Batal")

    def test_modal_close_with_x_button(self):
        """TC-FE-011: Memastikan modal edit bisa ditutup dengan tombol X"""
        # Arrange
        task_title = f"Modal X Test {time.time()}"
        self.page.create_task(task_title, "Test modal X", "pending")

        # Test: Tutup dengan tombol X
        self.page.click_edit_task(task_title)
        self.driver.find_element(*self.page.BTN_CLOSE_MODAL).click()

        wait = WebDriverWait(self.driver, 5)
        wait.until(EC.invisibility_of_element_located(self.page.MODAL_EDIT))

        modal = self.driver.find_element(*self.page.MODAL_EDIT)
        assert not modal.is_displayed(), "Modal masih tampil setelah klik X"
        print("✓ Modal bisa ditutup dengan tombol X")

    def test_empty_state_when_no_tasks(self):
        """TC-FE-012: Memastikan empty state muncul saat tidak ada tugas"""
        # Arrange - Hapus semua tugas via API
        tasks = requests.get(API_URL).json()
        for task in tasks:
            requests.delete(f"{API_URL}/{task['id']}")

        # Act - Refresh halaman
        self.page.refresh_tasks()

        # Assert
        assert self.page.is_empty_state_displayed(), "Empty state tidak muncul"
        empty_text = self.driver.find_element(*self.page.EMPTY_STATE).text
        assert "Belum ada tugas" in empty_text
        print("✓ Empty state ditampilkan dengan benar")

    def test_search_filters_tasks_by_keyword(self):
        """TC-FE-013: Pencarian menyaring tugas berdasarkan keyword"""
        # Arrange - buat 2 tugas dengan judul berbeda
        unique = str(int(time.time()))
        self.page.create_task(f"FINDME_{unique}", "bisa ditemukan", "pending")
        self.page.wait_for_alert_to_disappear()
        self.page.create_task(f"OTHER_{unique}", "tidak cocok", "pending")
        self.page.wait_for_alert_to_disappear()

        # Act - ketik keyword di search
        self.page.set_search(f"FINDME_{unique}")

        # Assert - hanya tugas yang cocok yang tampil
        titles = self.page.get_visible_titles()
        assert any(
            f"FINDME_{unique}" in t for t in titles
        ), "Tugas yang cocok tidak muncul"
        assert not any(
            f"OTHER_{unique}" in t for t in titles
        ), "Tugas yang tidak cocok ikut muncul"
        print("✓ Pencarian berhasil menyaring tugas berdasarkan keyword")

    def test_filter_by_status_shows_only_matching(self):
        """TC-FE-014: Filter status hanya menampilkan tugas dengan status yang dipilih"""
        # Arrange - buat tugas pending dan completed
        unique = str(int(time.time()))
        self.page.create_task(f"Pending_{unique}", "", "pending")
        self.page.wait_for_alert_to_disappear()
        self.page.create_task(f"Completed_{unique}", "", "completed")
        self.page.wait_for_alert_to_disappear()

        # Act - pilih filter "pending"
        self.page.set_filter_status("pending")

        # Assert - semua baris berstatus Pending
        tasks_shown = self.page.get_all_tasks()
        for task in tasks_shown:
            assert (
                task["status"].lower() == "pending"
            ), f"Tugas dengan status '{task['status']}' muncul padahal filter=pending"
        print("✓ Filter status hanya menampilkan tugas 'pending'")

    def test_search_empty_result_shows_no_match_message(self):
        """TC-FE-015: Pencarian tanpa hasil menampilkan pesan 'tidak ada'"""
        # Act - cari keyword yang pasti tidak ada
        self.page.set_search("XXXXXXXXXNOTEXIST_99999")

        # Assert - empty state dengan pesan pencarian
        import time as t

        t.sleep(0.5)
        container = self.driver.find_element(*self.page.EMPTY_STATE)
        assert container.is_displayed(), "Pesan kosong tidak muncul"
        assert (
            "tidak ada" in container.text.lower() or "cocok" in container.text.lower()
        ), f"Pesan tidak sesuai: '{container.text}'"
        print("✓ Pencarian tanpa hasil menampilkan pesan yang sesuai")

    def test_clear_search_restores_all_tasks(self):
        """TC-FE-016: Menghapus pencarian menampilkan kembali semua tugas"""
        # Arrange - pastikan ada setidaknya 1 tugas
        unique = str(int(time.time()))
        self.page.create_task(f"Restore_{unique}", "", "pending")
        self.page.wait_for_alert_to_disappear()
        total_before = self.page.get_visible_row_count()

        # Act - cari sesuatu lalu clear
        self.page.set_search("XXXXXXXXXNOTEXIST_99999")
        import time as t

        t.sleep(0.5)
        self.page.set_search("")

        # Assert - kembali ke jumlah semula
        total_after = self.page.get_visible_row_count()
        assert (
            total_after >= total_before
        ), "Jumlah tugas berkurang setelah clear search"
        print("✓ Menghapus pencarian menampilkan kembali semua tugas")
