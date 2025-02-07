import sys
import os
import requests
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QFileDialog, QProgressBar, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QIcon  # Import QIcon


class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()  # Raises HTTPError for bad responses
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0


            with open(self.save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        progress_percent = int((downloaded_size / total_size) * 100)
                        self.progress.emit(progress_percent)

            self.finished.emit("Download completed!")
        except requests.exceptions.RequestException as e:
            self.error.emit(f"Request error: {str(e)}")
        except Exception as e:
            self.error.emit(f"Unexpected error: {str(e)}")


class DownloadManager(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("sDownload Manager")
        self.setGeometry(300, 200, 500, 250)
        # Set window icon (favicon)
        self.setWindowIcon(QIcon("favicon.ico"))  # Change "icon.ico" to your icon file

        layout = QVBoxLayout()

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Enter file URL...")
        layout.addWidget(self.url_input)

        self.extension_input = QLineEdit(self)
        self.extension_input.setPlaceholderText("Optional: Enter desired file extension (e.g., .txt, .mp4)")
        layout.addWidget(self.extension_input)

        self.save_button = QPushButton("Choose Save Location", self)
        self.save_button.clicked.connect(self.choose_save_location)
        layout.addWidget(self.save_button)

        self.download_button = QPushButton("Download", self)
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("", self)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def choose_save_location(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "All Files (*.*)")
        if file_name:
            if self.extension_input.text():
                file_name += self.extension_input.text()
            self.save_path = file_name

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Warning", "Please enter a valid URL.")
            return

        if not hasattr(self, 'save_path') or not self.save_path:
            QMessageBox.warning(self, "Warning", "Please choose a save location.")
            return

        # Ensure URL ends with a file extension if specified
        if not self.extension_input.text() and not os.path.splitext(self.save_path)[1]:
            QMessageBox.warning(self, "Warning", "Please provide a file extension or make sure the URL points to a file.")
            return

        self.download_button.setEnabled(False)  # Disable download button during download
        self.status_label.setText("Downloading...")

        # Show a pop-up message while downloading
        self.in_progress_popup = QMessageBox(self)
        self.in_progress_popup.setIcon(QMessageBox.Icon.Information)
        self.in_progress_popup.setWindowTitle("Download in Progress")
        self.in_progress_popup.setText("Download is in progress. Please wait...")
        self.in_progress_popup.setStandardButtons(QMessageBox.StandardButton.NoButton)
        self.in_progress_popup.show()

        self.download_thread = DownloadThread(url, self.save_path)
        self.download_thread.progress.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.error.connect(self.download_error)
        self.download_thread.start()

    def download_finished(self, message):
        self.download_button.setEnabled(True)  # Re-enable the download button
        self.status_label.setText(message)
        self.in_progress_popup.close()  # Close the in-progress pop-up
        QMessageBox.information(self, "Success", message)
        self.progress_bar.setValue(100)

    def download_error(self, error_message):
        self.download_button.setEnabled(True)  # Re-enable the download button
        self.status_label.setText(f"Error: {error_message}")
        self.in_progress_popup.close()  # Close the in-progress pop-up
        QMessageBox.critical(self, "Error", f"Download failed: {error_message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DownloadManager()
    window.show()
    sys.exit(app.exec())
