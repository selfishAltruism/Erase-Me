import os
import sys
import time
import requests
from PIL import ImageGrab, Image
from dotenv import load_dotenv

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTabWidget, QMessageBox
)
from PyQt5.QtGui import QPixmap, QFontDatabase, QFont
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal


""" 
1. 마스킹 결과에 대해서 복사를 하게 되면, 일정 시간 (interrupt_delay) 동안 마스킹 자동 수행이 무시됨.
2. 첫 실행 시 클립보드를 확인하는 경우 마스킹 자동 수행이 무시됨. (프로그램 실행 시 바로 작동을 막기 위함)

TODO: 마스킹 탭을 강제 종료하는 경우, 에러가 걸림 => 메인 탭에서 종료 시 정상 작동
 """

# TODO: 발표 계획 맞춰서 변경 필요
interrupt_delay = 5000

class MaskingWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, server_url, img_path, save_path):
        super().__init__()
        self.server_url = server_url
        self.img_path = img_path
        self.save_path = save_path

    def run(self):
        try:
            with open(self.img_path, "rb") as f:
                res = requests.post(self.server_url, files={"image": f})
            if res.status_code == 200:
                with open(self.save_path, "wb") as out:
                    out.write(res.content)
                self.finished.emit(self.save_path)
            else:
                self.error.emit(f"❌ 서버 오류: {res.status_code}")
        except Exception as e:
            self.error.emit(f"❌ 요청 실패: {e}")

class ImageMaskingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Erase Me: Image Masking")
        self.resize(600, 500)

        # 환경변수 로드
        load_dotenv()
        self.server_url = os.getenv("IMG_MASKING_SERVER_URL")
        if not self.server_url:
            QMessageBox.critical(self, "에러", "❌ IMG_MASKING_SERVER_URL 환경 변수가 설정되지 않았습니다.")
            sys.exit(1)

        # 글꼴 등록 및 기본 폰트 설정
        font_id = QFontDatabase.addApplicationFont("./public/Pretendard-Regular.otf")
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            app_font = QFont(font_family)
            app_font.setPointSize(app_font.pointSize() + 1) 
            QApplication.setFont(app_font)

        # 레이아웃
        self.layout = QVBoxLayout()

        self.status_label = QLabel("🚧 이미지 클립보드 감시 중...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        # 탭
        self.tabs = QTabWidget()
        self.masked_image_label = QLabel("마스킹된 이미지가 여기에 표시됩니다.")
        self.masked_image_label.setAlignment(Qt.AlignCenter)
        self.tabs.addTab(self.masked_image_label, "마스킹 결과")
        self.layout.addWidget(self.tabs)

        # 클립보드 복사 버튼
        self.copy_button = QPushButton("마스킹 이미지 클립보드 복사")
        self.copy_button.setMinimumHeight(50)
        self.copy_button.clicked.connect(self.copy_image_to_clipboard)
        self.copy_button.setEnabled(False)
        self.layout.addWidget(self.copy_button)

        self.setLayout(self.layout)

        # 상태 변수
        clipboard = QApplication.clipboard()
        self.last_clip = clipboard.pixmap()  # macOS 호환을 위해 QClipboard 사용
        self.is_processing = False
        self.is_internal_copy = False

        # 타이머로 감시
        self.timer = QTimer()
        self.timer.timeout.connect(self.monitor_clipboard)
        self.timer.start(500)  # 0.5초마다 감시

    def monitor_clipboard(self):
        if self.is_processing or self.is_internal_copy:
            return  # 처리 중이거나 내부 복사 시 감시 중단

        clipboard = QApplication.clipboard()
        img = clipboard.pixmap()
        if img and not img.isNull() and img.toImage() != self.last_clip.toImage():
            self.last_clip = img
            img_path = "img/code.png"
            os.makedirs("img", exist_ok=True)
            img.save(img_path, "PNG")
            print(f"✅ 캡처 이미지 저장됨: {img_path}")

            # 창을 최상단에 띄우기
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.show()
            self.raise_()
            self.activateWindow()

            # UI 업데이트
            self.masked_image_label.setText("⏳ 서버로 이미지 전송 중...")
            self.copy_button.setEnabled(False)

            # 서버 요청 쓰레드 실행
            self.is_processing = True
            self.worker = MaskingWorker(
                self.server_url,
                img_path,
                "masked_result.png"
            )
            self.worker.finished.connect(self.update_masked_image)
            self.worker.error.connect(self.show_error)
            self.worker.start()

    def update_masked_image(self, path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.masked_image_label.setPixmap(
                pixmap.scaled(500, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self.copy_button.setEnabled(True)
        else:
            self.masked_image_label.setText("❌ 이미지 로딩 실패")
            self.copy_button.setEnabled(False)

        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()
        self.is_processing = False

        # 서버 응답 직후 내부 복사 방지 플래그 설정
        self.is_internal_copy = True
        QTimer.singleShot(interrupt_delay, self.reset_internal_copy)

    def reset_internal_copy(self):
        self.is_internal_copy = False

    def show_error(self, message):
        QMessageBox.critical(self, "에러", message)
        self.masked_image_label.setText("❌ 서버 요청 실패")
        self.copy_button.setEnabled(False)
        self.is_processing = False

        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    def copy_image_to_clipboard(self):
        clipboard = QApplication.clipboard()
        pixmap = self.masked_image_label.pixmap()
        if pixmap:
            clipboard.setPixmap(pixmap)
            self.last_clip = clipboard.pixmap()  # 내부 복사 이미지 등록 (macOS 호환)
            QMessageBox.information(self, "성공", "마스킹 이미지를 클립보드에 복사했습니다.")
        else:
            QMessageBox.warning(self, "오류", "❌ 복사할 이미지가 없습니다.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageMaskingApp()
    window.show()
    sys.exit(app.exec_())