import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QComboBox, QTabWidget, QToolBar, QAction,
                             QTabBar, QMenu, QStatusBar, QMenuBar, QDialog, QFormLayout,
                             QCheckBox, QSpinBox, QLabel, QDialogButtonBox, QGroupBox, QTableView, QFileDialog,
                             QListWidget, QAbstractItemView, QMessageBox)
from PyQt5.QtCore import QUrl, QSettings, Qt, QTimer, QStandardPaths, QAbstractTableModel, QVariant, QProcess
from PyQt5.QtGui import QIcon, QMouseEvent, QColor
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEnginePage, QWebEngineProfile
import os


class Browser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Shield Browser")
        self.setGeometry(100, 100, 1200, 800)

        self.setWindowIcon(QIcon("favicon.ico"))

        self.settings = QSettings("MyBrowser", "Settings")
        self.tabs = []
        self.history_stack = []
        self.current_history_index = -1
        self.is_dark_mode = False
        self.bookmarks = []  # List to store bookmarks
        self.download_history = []  # List to store download history

        layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Toolbar
        toolbar = QToolBar()
        layout.addWidget(toolbar)

        # Back and Forward Buttons
        back_action = QAction(QIcon.fromTheme("go-previous"), "Back", self)
        back_action.triggered.connect(self.navigate_back)
        toolbar.addAction(back_action)

        forward_action = QAction(QIcon.fromTheme("go-next"), "Forward", self)
        forward_action.triggered.connect(self.navigate_forward)
        toolbar.addAction(forward_action)

        # Reload and Home Buttons
        reload_action = QAction(QIcon.fromTheme("view-refresh"), "Reload", self)
        reload_action.triggered.connect(self.reload_page)
        toolbar.addAction(reload_action)

        home_action = QAction(QIcon.fromTheme("go-home"), "Home", self)
        home_action.triggered.connect(self.go_home)
        toolbar.addAction(home_action)

        toolbar.addSeparator()

        # New Tab Button
        add_tab_action = QAction(QIcon.fromTheme("document-new"), "New Tab", self)
        add_tab_action.triggered.connect(self.add_new_tab)
        toolbar.addAction(add_tab_action)

        # Search Bar and Engine Combo
        self.search_bar = QLineEdit()
        toolbar.addWidget(self.search_bar)

        self.search_engine_combo = QComboBox()
        toolbar.addWidget(self.search_engine_combo)

        search_engines = {
            "Google": "https://www.google.com/search?q=",
            "DuckDuckGo": "https://duckduckgo.com/?q=",
            "Startpage": "https://www.startpage.com/sp/search?q=",
            "Yahoo": "https://search.yahoo.com/search?p=",
            "Ecosia": "https://www.ecosia.org/search?q=",
            "Brave": "https://search.brave.com/search?q=",  # Added Brave Search Engine
            "Visit URL": ""  # Added option for direct URL visit
        }

        self.search_engine_combo.addItems(list(search_engines.keys()))
        self.search_engine_combo.setCurrentText(self.settings.value("default_search_engine", "Google"))
        self.search_engines = search_engines

        search_button = QPushButton("Search")
        search_button.clicked.connect(self.search)
        toolbar.addWidget(search_button)

        self.search_bar.returnPressed.connect(self.search)

        # Zoom and Dark Mode Buttons (One row below the search bar)
        zoom_layout = QHBoxLayout()
        layout.addLayout(zoom_layout)

        zoom_in_button = self.create_uniform_button("Zoom In", "zoom-in", self.zoom_in)
        zoom_layout.addWidget(zoom_in_button)

        zoom_out_button = self.create_uniform_button("Zoom Out", "zoom-out", self.zoom_out)
        zoom_layout.addWidget(zoom_out_button)

        dark_mode_button = self.create_uniform_button("Dark Mode", "preferences-desktop-dark-theme",
                                                      self.toggle_dark_mode)
        zoom_layout.addWidget(dark_mode_button)

        download_button = self.create_uniform_button("Download", "download", self.open_downloads_folder)
        zoom_layout.addWidget(download_button)

        bookmark_button = self.create_uniform_button("Bookmark", "bookmark-new", self.toggle_bookmark)
        zoom_layout.addWidget(bookmark_button)

        bookmark_manager_button = self.create_uniform_button("Manage Bookmarks", None, self.open_bookmark_manager)
        zoom_layout.addWidget(bookmark_manager_button)

        # Download Manager Button
        download_manager_button = self.create_uniform_button("Download Manager", None, self.execute_download_manager)
        zoom_layout.addWidget(download_manager_button)

        # Tab Widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self.tab_widget.setTabBar(CustomTabBar(self.tab_widget))

        self.add_new_tab()

        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Initialize with the correct mode
        self.apply_theme()

    def create_uniform_button(self, text, icon_name, callback):
        button = QPushButton(text)
        if icon_name:
            button.setIcon(QIcon.fromTheme(icon_name))
        button.clicked.connect(callback)
        button.setStyleSheet(""" 
            QPushButton {
                background-color: white;
                color: black;
                border: 1px solid black;
                border-radius: 5px;
                padding: 5px;
                margin: 3px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        return button

    def search(self):
        url = self.search_bar.text()

        # Get selected search engine or direct URL option
        selected_engine = self.search_engine_combo.currentText()

        # If "Visit URL" is selected, load the URL directly
        if selected_engine == "Visit URL":
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "http://" + url  # Add http:// if no scheme is provided
            current_webview = self.tab_widget.currentWidget()
            if current_webview:
                current_webview.load(QUrl(url))
        else:
            # Otherwise, use the selected search engine to search
            base_url = self.search_engines[selected_engine]
            url = base_url + url
            current_webview = self.tab_widget.currentWidget()
            if current_webview:
                current_webview.load(QUrl(url))

        self.settings.setValue("default_search_engine", selected_engine)

    def add_new_tab(self, url=None):
        webview = QWebEngineView()
        webview.loadFinished.connect(lambda ok: self.update_tab_title(self.tab_widget.indexOf(webview), webview))

        settings = webview.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        index = self.tab_widget.addTab(webview, "Loading...")
        self.tab_widget.setCurrentIndex(index)
        self.tabs.append(webview)

        if url:
            webview.load(QUrl(url))
        else:
            webview.load(QUrl("https://www.google.com"))

    def update_tab_title(self, index, webview):
        title = webview.page().title() or "New Tab"
        icon = webview.page().icon() or QIcon()
        self.tab_widget.setTabIcon(index, icon)
        self.tab_widget.setTabText(index, title)

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            webview_to_close = self.tab_widget.widget(index)
            self.tab_widget.removeTab(index)
            self.tabs.remove(webview_to_close)
            webview_to_close.deleteLater()

    def navigate_back(self):
        current_webview = self.tab_widget.currentWidget()
        if current_webview and current_webview.history().canGoBack():
            current_webview.back()

    def navigate_forward(self):
        current_webview = self.tab_widget.currentWidget()
        if current_webview and current_webview.history().canGoForward():
            current_webview.forward()

    def reload_page(self):
        current_webview = self.tab_widget.currentWidget()
        if current_webview:
            current_webview.reload()

    def go_home(self):
        current_webview = self.tab_widget.currentWidget()
        if current_webview:
            current_webview.load(QUrl("https://www.google.com"))

    def zoom_in(self):
        current_webview = self.tab_widget.currentWidget()
        if current_webview:
            current_zoom = current_webview.zoomFactor()
            current_webview.setZoomFactor(current_zoom + 0.1)

    def zoom_out(self):
        current_webview = self.tab_widget.currentWidget()
        if current_webview:
            current_zoom = current_webview.zoomFactor()
            current_webview.setZoomFactor(current_zoom - 0.1)

    def toggle_dark_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def apply_theme(self):
        if self.is_dark_mode:
            self.setStyleSheet("""
                QWidget {
                    background-color: #2E2E2E;
                    color: white;
                }
                QLineEdit, QComboBox, QPushButton {
                    background-color: #555;
                    color: white;
                    border: 1px solid #333;
                }
                QPushButton:hover {
                    background-color: #777;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: white;
                    color: black;
                }
                QLineEdit, QComboBox, QPushButton {
                    background-color: #f0f0f0;
                    color: black;
                    border: 1px solid #ccc;
                }
                QPushButton:hover {
                    background-color: #ddd;
                }
            """)

    def open_bookmark_manager(self):
        dialog = BookmarkManager(self, self.bookmarks)
        dialog.exec_()

    def toggle_bookmark(self):
        current_webview = self.tab_widget.currentWidget()
        if current_webview:
            url = current_webview.url().toString()
            title = current_webview.page().title()

            if url not in [bm[1] for bm in self.bookmarks]:
                self.bookmarks.append((title, url))
            else:
                self.bookmarks = [bm for bm in self.bookmarks if bm[1] != url]

    def open_downloads_folder(self):
        """Opens the system's Downloads folder."""
        download_path = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)

        if os.path.exists(download_path):  # Ensure the path exists
            if sys.platform.startswith("win"):
                os.startfile(download_path)  # Windows
            elif sys.platform.startswith("darwin"):
                os.system(f'open "{download_path}"')  # macOS
            else:
                os.system(f'xdg-open "{download_path}"')  # Linux
        else:
            QMessageBox.warning(self, "Error", "Download folder not found.")

    def execute_download_manager(self):
        # Executes the external download manager
        download_manager_path = os.path.join(os.path.dirname(__file__), 'Download_manager.py')
        process = QProcess(self)
        process.start(f'python "{download_manager_path}"')


class BookmarkManager(QDialog):
    def __init__(self, parent=None, bookmarks=None):
        super().__init__(parent)
        self.setWindowTitle("Bookmark Manager")
        self.setGeometry(300, 200, 400, 300)

        self.layout = QVBoxLayout(self)

        # List widget to display the bookmarks
        self.bookmark_list = QListWidget(self)
        self.layout.addWidget(self.bookmark_list)

        # Button to visit selected bookmark
        self.visit_button = QPushButton("Visit", self)
        self.visit_button.clicked.connect(self.visit_bookmark)
        self.layout.addWidget(self.visit_button)

        # Button to remove selected bookmark
        self.remove_button = QPushButton("Remove", self)
        self.remove_button.clicked.connect(self.remove_selected_bookmark)
        self.layout.addWidget(self.remove_button)

        # Initialize bookmarks list
        self.bookmarks = bookmarks if bookmarks else []
        self.load_bookmarks()

    def load_bookmarks(self):
        """Load bookmarks and display them in the list."""
        self.bookmark_list.clear()
        for title, url in self.bookmarks:
            self.bookmark_list.addItem(f"{title} - {url}")

    def add_bookmark(self, title, url):
        """Add a new bookmark and refresh the list."""
        self.bookmarks.append((title, url))
        self.load_bookmarks()

    def visit_bookmark(self):
        """Visit the selected bookmark."""
        selected_items = self.bookmark_list.selectedItems()
        for item in selected_items:
            bookmark = item.text().split(" - ")
            url = bookmark[1]

            # Here, we simulate opening the URL in a new tab in a browser
            # You should replace this with actual browser functionality in your project
            print(f"Visiting: {url}")  # This simulates opening a URL in a new tab

    def remove_selected_bookmark(self):
        """Remove the selected bookmark(s) after confirmation."""
        selected_items = self.bookmark_list.selectedItems()
        if selected_items:
            for item in selected_items:
                bookmark = item.text().split(" - ")
                url = bookmark[1]

                # Confirm deletion for each selected bookmark
                confirmation = QMessageBox.question(self, "Confirm Removal",
                                                    f"Are you sure you want to remove the bookmark '{bookmark[0]}'?",
                                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

                if confirmation == QMessageBox.Yes:
                    # Remove the bookmark
                    self.bookmarks = [bm for bm in self.bookmarks if bm[1] != url]
            self.load_bookmarks()  # Reload the updated bookmark list

    def exec_(self):
        """Override exec_ to make sure the dialog is modal."""
        super().exec_()
        self.setModal(True)
        self.raise_()  # Ensure it pops up above all other windows


class CustomTabBar(QTabBar):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("""
            QTabBar::tab {
                background-color: #F0F0F0;
                color: black;
                padding: 10px;
                border: 1px solid #CCC;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #D0D0D0;
            }
            QTabBar::tab:hover {
                background-color: #E0E0E0;
            }
        """)

class DownloadManager(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Download Manager")
        self.setGeometry(300, 200, 500, 400)
        layout = QVBoxLayout(self)

        self.download_history_view = QTableView(self)
        layout.addWidget(self.download_history_view)

        self.download_history_view.setModel(self.create_download_history_model())

    def create_download_history_model(self):
        class DownloadHistoryModel(QAbstractTableModel):
            def __init__(self, data):
                super().__init__()
                self.data = data

            def rowCount(self, parent):
                return len(self.data)

            def columnCount(self, parent):
                return len(self.data[0]) if self.data else 0

            def data(self, index, role):
                if role == Qt.DisplayRole:
                    return QVariant(self.data[index.row()][index.column()])

        data = [(download["file"], download["url"], download["status"]) for download in self.parent().download_history]
        return DownloadHistoryModel(data)

    def show_download_manager(self):
        self.exec_()


app = QApplication(sys.argv)
window = Browser()
window.show()
app.exec_()
