from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QMessageBox, QApplication
from PyQt5.QtCore import QUrl



class BookmarkManager(QDialog):
    def __init__(self, parent=None, bookmarks=None):
        super().__init__(parent)
        self.setWindowTitle("Bookmark Manager")
        self.setGeometry(300, 200, 400, 300)
        self.setWindowIcon(QIcon("favicon.ico"))

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

            # Actual browser tab opening should be implemented in the parent
            # current_webview = self.parent().tab_widget.currentWidget()
            # if current_webview:
            #     current_webview.load(QUrl(url))

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


# Test the BookmarkManager when run separately
if __name__ == "__main__":
    app = QApplication([])
    bookmarks = [("Google", "https://www.google.com"), ("PyQt5", "https://www.riverbankcomputing.com/software/pyqt/intro")]
    window = BookmarkManager(bookmarks=bookmarks)
    window.exec_()
