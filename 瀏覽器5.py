import sys
import json
import os
from PyQt5.QtCore import QUrl, QStandardPaths
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QVBoxLayout, QWidget, QToolBar, QAction, QTabWidget, QMenu, QListWidget, QDialog, QLabel, QProgressBar, QInputDialog, QMessageBox, QCheckBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem, QWebEngineProfile
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtGui import QIcon

class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)

    def interceptRequest(self, info):
        # 攔截包含廣告關鍵字的請求
        if any(ad in info.requestUrl().toString() for ad in ["ads", "doubleclick", "adservice"]):
            info.block(True)

class SimpleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        # 設置窗口標題
        self.setWindowTitle("簡易瀏覽器")
        # self.setWindowIcon(QIcon("browser_icon.png"))  # 如果需要圖標，取消註釋

        # 初始化設置
        self.home_page = "https://www.google.com"
        self.default_search_engine = "https://www.google.com/search?q="
        self.is_private_mode = False
        self.is_dark_mode = False
        self.ad_blocker_enabled = True

        # 初始化用戶數據
        self.bookmarks = []
        self.history = []
        self.saved_passwords = {}
        self.load_user_data()

        # 創建多標籤頁面
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        # 創建導航工具欄
        self.create_toolbar()

        # 添加第一個標籤頁
        self.add_new_tab(QUrl(self.home_page), "首頁")

        # 下載管理器
        self.downloads = []

    def create_toolbar(self):
        """創建導航工具欄"""
        navtb = QToolBar("導航")
        self.addToolBar(navtb)

        # 添加按鈕：後退、前進、刷新、主頁
        back_btn = QAction("後退", self)
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        navtb.addAction(back_btn)

        next_btn = QAction("前進", self)
        next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        navtb.addAction(next_btn)

        reload_btn = QAction("刷新", self)
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        navtb.addAction(reload_btn)

        home_btn = QAction("主頁", self)
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)

        # 地址欄
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        navtb.addWidget(self.urlbar)

        # 書籤按鈕
        bookmark_btn = QAction("書籤", self)
        bookmark_btn.triggered.connect(self.add_bookmark)
        navtb.addAction(bookmark_btn)

        # 歷史記錄按鈕
        history_btn = QAction("歷史記錄", self)
        history_btn.triggered.connect(self.show_history)
        navtb.addAction(history_btn)

        # 下載按鈕
        download_btn = QAction("下載", self)
        download_btn.triggered.connect(self.show_downloads)
        navtb.addAction(download_btn)

        # 新標籤頁按鈕
        new_tab_btn = QAction("新標籤頁", self)
        new_tab_btn.triggered.connect(lambda: self.add_new_tab())
        navtb.addAction(new_tab_btn)

        # 隱私模式按鈕
        private_btn = QAction("隱私模式", self)
        private_btn.triggered.connect(self.toggle_private_mode)
        navtb.addAction(private_btn)

        # 設置按鈕
        settings_btn = QAction("設置", self)
        settings_btn.triggered.connect(self.show_settings)
        navtb.addAction(settings_btn)

        # 主題切換按鈕
        theme_btn = QAction("切換主題", self)
        theme_btn.triggered.connect(self.toggle_theme)
        navtb.addAction(theme_btn)

    def add_new_tab(self, url=None, label="新標籤頁"):
        """添加新標籤頁"""
        if url is None:
            url = QUrl(self.home_page)

        browser = QWebEngineView()
        browser.setUrl(url)
        browser.urlChanged.connect(self.update_urlbar)
        browser.loadFinished.connect(self.update_title)
        browser.page().profile().downloadRequested.connect(self.download_requested)

        # 啟用廣告攔截
        if self.ad_blocker_enabled:
            interceptor = AdBlocker()
            browser.page().profile().setUrlRequestInterceptor(interceptor)

        index = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(index)

    def close_tab(self, index):
        """關閉標籤頁"""
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def navigate_to_url(self):
        """導航到地址欄中的URL"""
        query = self.urlbar.text()
        if " " in query or "." not in query:  # 如果輸入的是搜索關鍵詞
            url = self.default_search_engine + query
        else:  # 如果輸入的是URL
            url = query if query.startswith("http") else "http://" + query
        self.tabs.currentWidget().setUrl(QUrl(url))

    def navigate_home(self):
        """導航到主頁"""
        self.tabs.currentWidget().setUrl(QUrl(self.home_page))

    def update_urlbar(self, q):
        """更新地址欄"""
        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)
        if not self.is_private_mode:
            self.history.append(q.toString())
            self.save_user_data()

    def update_title(self):
        """更新標籤頁標題"""
        title = self.tabs.currentWidget().page().title()
        self.tabs.setTabText(self.tabs.currentIndex(), title[:15] + "...")

    def add_bookmark(self):
        """添加書籤"""
        url = self.tabs.currentWidget().url().toString()
        if url not in self.bookmarks:
            self.bookmarks.append(url)
            self.save_user_data()
            QMessageBox.information(self, "書籤已添加", f"已添加書籤: {url}")

    def show_history(self):
        """顯示歷史記錄"""
        history_dialog = QDialog(self)
        history_dialog.setWindowTitle("歷史記錄")
        layout = QVBoxLayout()
        history_list = QListWidget()
        for url in self.history:
            history_list.addItem(url)
        layout.addWidget(history_list)
        history_dialog.setLayout(layout)
        history_dialog.exec_()

    def download_requested(self, download: QWebEngineDownloadItem):
        """處理下載請求"""
        download_path = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        download.setPath(download_path + "/" + download.suggestedFileName())
        download.accept()
        self.downloads.append(download)
        self.show_downloads()

    def show_downloads(self):
        """顯示下載管理器"""
        download_dialog = QDialog(self)
        download_dialog.setWindowTitle("下載")
        layout = QVBoxLayout()
        for download in self.downloads:
            label = QLabel(download.path())
            progress = QProgressBar()
            progress.setValue(download.progress())
            layout.addWidget(label)
            layout.addWidget(progress)
        download_dialog.setLayout(layout)
        download_dialog.exec_()

    def toggle_private_mode(self):
        """切換隱私模式"""
        self.is_private_mode = not self.is_private_mode
        if self.is_private_mode:
            QMessageBox.information(self, "隱私模式", "隱私模式已開啟。歷史記錄和Cookies將不會被保存。")
        else:
            QMessageBox.information(self, "隱私模式", "隱私模式已關閉。歷史記錄和Cookies將會被保存。")

    def toggle_theme(self):
        """切換主題"""
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.setStyleSheet("""
                QMainWindow { background-color: #333; color: #FFF; }
                QToolBar { background-color: #444; color: #FFF; }
                QLineEdit { background-color: #555; color: #FFF; }
                QTabWidget::pane { background-color: #333; color: #FFF; }
                QTabBar::tab { background-color: #444; color: #FFF; }
            """)
        else:
            self.setStyleSheet("")  # 恢復默認樣式
        QMessageBox.information(self, "主題已更改", f"主題已設置為 {'暗黑' if self.is_dark_mode else '明亮'} 模式。")

    def show_settings(self):
        """顯示設置頁面"""
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("設置")
        layout = QVBoxLayout()

        # 設置主頁
        home_page_btn = QAction("設置主頁", self)
        home_page_btn.triggered.connect(self.set_home_page)
        layout.addWidget(home_page_btn)

        # 設置搜索引擎
        search_engine_btn = QAction("設置搜索引擎", self)
        search_engine_btn.triggered.connect(self.set_search_engine)
        layout.addWidget(search_engine_btn)

        # 廣告攔截開關
        ad_blocker_checkbox = QCheckBox("啟用廣告攔截", self)
        ad_blocker_checkbox.setChecked(self.ad_blocker_enabled)
        ad_blocker_checkbox.stateChanged.connect(self.toggle_ad_blocker)
        layout.addWidget(ad_blocker_checkbox)

        settings_dialog.setLayout(layout)
        settings_dialog.exec_()

    def set_home_page(self):
        """設置主頁"""
        new_home_page, ok = QInputDialog.getText(self, "設置主頁", "請輸入主頁的URL：")
        if ok:
            self.home_page = new_home_page
            QMessageBox.information(self, "主頁已更新", f"主頁已設置為: {new_home_page}")

    def set_search_engine(self):
        """設置搜索引擎"""
        engines = {
            "Google": "https://www.google.com/search?q=",
            "Bing": "https://www.bing.com/search?q=",
            "DuckDuckGo": "https://duckduckgo.com/?q="
        }
        engine, ok = QInputDialog.getItem(self, "設置搜索引擎", "請選擇搜索引擎：", engines.keys(), 0, False)
        if ok:
            self.default_search_engine = engines[engine]
            QMessageBox.information(self, "搜索引擎已更新", f"搜索引擎已設置為: {engine}")

    def toggle_ad_blocker(self, state):
        """切換廣告攔截器"""
        self.ad_blocker_enabled = state == 2  # 2 表示選中
        QMessageBox.information(self, "廣告攔截器", f"廣告攔截器已 {'啟用' if self.ad_blocker_enabled else '停用'}。")

    def load_user_data(self):
        """加載用戶數據"""
        data_path = os.path.join(QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation), "user_data.json")
        try:
            with open(data_path, "r") as file:
                data = json.load(file)
                self.bookmarks = data.get("bookmarks", [])
                self.history = data.get("history", [])
                self.saved_passwords = data.get("passwords", {})
        except FileNotFoundError:
            pass

    def save_user_data(self):
        """保存用戶數據"""
        data_path = os.path.join(QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation), "user_data.json")
        data = {
            "bookmarks": self.bookmarks,
            "history": self.history,
            "passwords": self.saved_passwords
        }
        with open(data_path, "w") as file:
            json.dump(data, file)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimpleBrowser()
    window.show()
    sys.exit(app.exec_())
