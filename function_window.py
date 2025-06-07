import sys
import os
import json
import subprocess
import signal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFileDialog
)
from PyQt5.QtGui import QPixmap, QFont, QFontDatabase
from PyQt5.QtCore import Qt

class FunctionWindow(QWidget):
    def __init__(self, back_callback=None):
        super().__init__()
        self.back_callback = back_callback
        self.mask_targets = []

        self.text_proc = None
        self.img_proc = None

        self.reload_selected_fields()
        self.initUI()

    def reload_selected_fields(self):
        if os.path.exists("selected_fields.json"):
            with open("selected_fields.json", "r", encoding="utf-8") as f:
                self.mask_targets = json.load(f)
        else:
            self.mask_targets = []

        print("불러온 마스킹 대상:", self.mask_targets)

    def initUI(self):
        logo = QPixmap("./public/logo.png")
        self.logo_label = QLabel()
        self.logo_label.setPixmap(logo.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo_label.setAlignment(Qt.AlignCenter)

        # 텍스트 클릭보드 마스킹 활성화 버튼
        # TODO: 식별자 이름 정리 필요
        self.btn_text = QPushButton("텍스트 자동 마스킹")
        self.btn_text.setCheckable(True)
        self.btn_text.setFixedSize(450, 50)
        self.btn_text.clicked.connect(self.toggle_text_masking_process)
        self.btn_text.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #3e5879;
                font-weight: bold;
                font-size: 18px;
                font-family: Pretendard;
                border: 1px solid #3e5879;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:checked {
                background-color: #3e5879;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #acbacb;
            }
        """)


        # 이미지 클릭보드 마스킹 활성화 버튼
        self.btn_image_masking = QPushButton("이미지 자동 마스킹")
        self.btn_image_masking.setCheckable(True)
        self.btn_image_masking.setFixedSize(450, 50)
        self.btn_image_masking.clicked.connect(self.toggle_image_masking_process)
        self.btn_image_masking.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #3e5879;
                font-weight: bold;
                font-size: 18px;
                font-family: Pretendard;
                border: 1px solid #3e5879;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:checked {
                background-color: #3e5879;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #acbacb;
            }
        """)


        # 이미지 & 음성 마스킹 결과 탭 선택 버튼
        self.btn_image = QPushButton("이미지 탭")
        self.btn_voice = QPushButton("음성 탭")
        self.btn_image.setCheckable(True)
        self.btn_voice.setCheckable(True)
        self.btn_image.setChecked(True)

        self.btn_image.setFixedSize(450, 50)
        self.btn_voice.setFixedSize(450, 50)
        self.btn_image.clicked.connect(self.select_image)
        self.btn_voice.clicked.connect(self.select_voice)
        self.update_button_style()

        self.stack = QStackedWidget()
        self.image_page = self.build_image_page()
        self.voice_page = self.build_voice_page()
        self.stack.addWidget(self.image_page)
        self.stack.addWidget(self.voice_page)

        hbox_masking = QHBoxLayout()
        hbox_masking.setSpacing(10)
        hbox_masking.setContentsMargins(0, 10, 0, 0)
        hbox_masking.addWidget(self.btn_text)
        hbox_masking.addWidget(self.btn_image_masking)

        hbox_result_tap = QHBoxLayout()
        hbox_result_tap.setSpacing(10)
        hbox_result_tap.setContentsMargins(0, 20, 0, 0)
        hbox_result_tap.addWidget(self.btn_image)
        hbox_result_tap.addWidget(self.btn_voice)

        vbox = QVBoxLayout()
        vbox.setSpacing(0)
        vbox.setContentsMargins(20, 20, 20, 20)
        vbox.addWidget(self.logo_label)
        vbox.addLayout(hbox_masking)
        vbox.addLayout(hbox_result_tap)

        vbox.addWidget(self.stack)

        # TODO: 탭 디자인 변경
        self.stack.setStyleSheet("""
            QStackedWidget {
                background-color: #ffffff;
                border: 1px solid #3e5879;
                border-radius: 8px;
            }
        """)

        vbox.addSpacing(20)
        redo_btn = QPushButton("마스킹 범위 재설정")
        redo_btn.setFixedSize(170, 50)
        redo_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #3e5879;
                font-weight: bold;
                font-size: 15px;
                font-family: Pretendard;
                border: 1px solid #3e5879;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #acbacb;
            }
        """)
        redo_btn.clicked.connect(self.handle_back_to_selection)
        vbox.addWidget(redo_btn, alignment=Qt.AlignRight)

        self.setLayout(vbox)
        self.setWindowTitle("Erase Me")
        self.resize(1000, 700)
        self.stack.setCurrentIndex(0)
        self.show()

    def toggle_text_masking_process(self):
        if self.btn_text.isChecked():
            script_path = os.path.abspath("./masking/text_masking.py")
            self.text_proc = subprocess.Popen(
                [sys.executable, script_path],
                stderr=subprocess.DEVNULL
            )
            print("🚀 텍스트 마스킹 프로그램 실행됨")
            self.btn_text.setText("텍스트 자동 마스킹 (ON)")
        else:
            if self.text_proc:
                self.text_proc.terminate()
                self.text_proc = None
                print("🛑 텍스트 마스킹 프로그램 종료됨")
            self.btn_text.setText("텍스트 자동 마스킹 (OFF)")

    def toggle_image_masking_process(self):
        if self.btn_image_masking.isChecked():
            self.update_button_style()
            
            if self.img_proc is None:
                script_path = os.path.abspath("./masking/img_masking.py")
                self.img_proc = subprocess.Popen(
                    [sys.executable, script_path],
                    stderr=subprocess.DEVNULL
                )
                print("🚀 이미지 마스킹 프로그램 실행됨")
                self.btn_image_masking.setText("이미지 자동 마스킹 (ON)")
            else:
                print("이미 이미지 마스킹 프로그램이 실행 중입니다.")
        else:
            self.update_button_style()
            if self.img_proc:
                self.img_proc.terminate()
                self.img_proc = None
                print("🛑 이미지 마스킹 프로그램 종료됨")
            self.btn_image_masking.setText("이미지 자동 마스킹 (OFF)")
        
    def handle_back_to_selection(self):
        if os.path.exists("selected_fields.json"):
            os.remove("selected_fields.json")
        if self.back_callback:
            self.back_callback()

    def build_image_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        label = QLabel("🖼️ 이미지 업로드")
        label.setAlignment(Qt.AlignCenter)

        self.img_file_label = QLabel("선택된 파일 없음")
        self.img_file_label.setAlignment(Qt.AlignCenter)

        upload_btn = QPushButton("이미지 선택")
        upload_btn.setFixedWidth(200)
        upload_btn.clicked.connect(self.upload_image)

        self.img_preview = QLabel()
        self.img_preview.setFixedSize(200, 200)
        self.img_preview.setAlignment(Qt.AlignCenter)
        self.img_preview.hide()

        self.copy_btn = QPushButton("마스킹 이미지 복사")
        self.copy_btn.setFixedWidth(200)
        self.copy_btn.clicked.connect(self.copy_preview_image_to_clipboard)
        self.copy_btn.hide()

        layout.addWidget(label)
        layout.addWidget(upload_btn)
        layout.addWidget(self.img_file_label)
        layout.addWidget(self.img_preview, alignment=Qt.AlignCenter)
        layout.addWidget(self.copy_btn, alignment=Qt.AlignCenter)

        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def build_voice_page(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        label = QLabel("🎤 음성 파일 업로드")
        label.setAlignment(Qt.AlignCenter)

        self.voice_file_label = QLabel("선택된 파일 없음")
        self.voice_file_label.setAlignment(Qt.AlignCenter)

        upload_btn = QPushButton("음성 파일 선택")
        upload_btn.setFixedWidth(200)
        upload_btn.clicked.connect(self.upload_voice)

        layout.addWidget(label)
        layout.addWidget(upload_btn, alignment=Qt.AlignCenter)
        layout.addWidget(self.voice_file_label)

        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "이미지 선택", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.img_file_label.setText(f"선택된 이미지: {file_path.split('/')[-1]}")
            pixmap = QPixmap(file_path).scaled(
                200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.img_preview.setPixmap(pixmap)
            self.img_preview.show()
            self.copy_btn.show()
        else:
            self.img_file_label.setText("선택된 파일 없음")
            self.img_preview.clear()
            self.img_preview.hide()
            self.copy_btn.hide()
    
    def copy_preview_image_to_clipboard(self):
        if not self.img_preview.pixmap():
            return
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(self.img_preview.pixmap())
        print("✅ 미리보기 이미지를 클립보드에 복사했습니다.")

    def upload_voice(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "음성 선택", "", "Audio Files (*.mp3 *.wav *.m4a)")
        if file_path:
            self.voice_file_label.setText(f"선택된 음성: {file_path.split('/')[-1]}")

    # 이미지 버튼 이벤트 핸들러
    def select_image(self):
        self.btn_image.setChecked(True)
        self.btn_voice.setChecked(False)
        self.stack.setCurrentIndex(0)
        self.update_button_style()

    def select_voice(self):
        self.btn_voice.setChecked(True)
        self.btn_image.setChecked(False)
        self.stack.setCurrentIndex(1)
        self.update_button_style()
    
    def closeEvent(self, event):
        if self.text_proc:
            self.text_proc.terminate()
            print("🛑 텍스트 마스킹 프로세스도 함께 종료됨")
        event.accept()

    def update_button_style(self):
        active = """
            QPushButton {
                background-color: #3e5879;
                color: white;
                font-weight: bold;
                font-size: 18px;
                font-family: Pretendard;
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #576981;
            }
        """
        inactive = """
            QPushButton {
                background-color: #F2F2F2;
                color: #3e5879;
                font-weight: bold;
                font-size: 18px;
                font-family: Pretendard;
                border: 1px solid #3e5879;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #acbacb;
            }
        """

        self.btn_image.setStyleSheet(active if self.btn_image.isChecked() else inactive)
        self.btn_voice.setStyleSheet(active if self.btn_voice.isChecked() else inactive)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    font_id = QFontDatabase.addApplicationFont("./public/Pretendard-Regular.otf")
    if font_id == -1:
        print("❌ Pretendard 폰트 로딩 실패")
    else:
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if font_families:
            app.setFont(QFont(font_families[0], 12))
    
    ex = FunctionWindow()
    sys.exit(app.exec_())
