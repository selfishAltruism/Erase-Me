import sys
import os
import json
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
        logo = QPixmap("logo.png")
        self.logo_label = QLabel()
        self.logo_label.setPixmap(logo.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo_label.setAlignment(Qt.AlignCenter)

        self.btn_image = QPushButton("이미지")
        self.btn_voice = QPushButton("음성")
        self.btn_image.setCheckable(True)
        self.btn_voice.setCheckable(True)
        self.btn_image.setChecked(True)
        self.btn_image.setFixedSize(300, 50)
        self.btn_voice.setFixedSize(300, 50)
        self.btn_image.clicked.connect(self.select_image)
        self.btn_voice.clicked.connect(self.select_voice)
        self.update_button_style()

        self.stack = QStackedWidget()
        self.image_page = self.build_image_page()
        self.voice_page = self.build_voice_page()
        self.stack.addWidget(self.image_page)
        self.stack.addWidget(self.voice_page)

        hbox = QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(self.btn_image)
        hbox.addWidget(self.btn_voice)

        vbox = QVBoxLayout()
        vbox.addWidget(self.logo_label)
        vbox.addLayout(hbox)
        vbox.addWidget(self.stack)

        redo_btn = QPushButton("선택 다시하기")
        redo_btn.setFixedSize(150, 40)
        redo_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #3e5879;
                font-weight: bold;
                font-size: 15px;
                font-family: Pretendard;
                border: 1px solid #3e5879;
                border-radius: 15px;
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

        # 이미지 미리보기 QLabel 생성
        self.img_preview = QLabel()
        self.img_preview.setFixedSize(200, 200)
        self.img_preview.setAlignment(Qt.AlignCenter)
        #self.img_preview.setStyleSheet("border: 1px solid gray;")
        self.img_preview.hide()  # 처음엔 숨김

        layout.addWidget(label)
        layout.addWidget(upload_btn)
        layout.addWidget(self.img_file_label)
        layout.addWidget(self.img_preview, alignment=Qt.AlignCenter)

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
            self.img_preview.show()  # 선택 후 보이기
        else:
            self.img_file_label.setText("선택된 파일 없음")
            self.img_preview.clear()
            self.img_preview.hide()  # 선택 취소 시 숨기기

    def upload_voice(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "음성 선택", "", "Audio Files (*.mp3 *.wav *.m4a)")
        if file_path:
            self.voice_file_label.setText(f"선택된 음성: {file_path.split('/')[-1]}")

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

    def update_button_style(self):
        active = """
            QPushButton {
                background-color: #3e5879;
                color: white;
                font-weight: bold;
                font-size: 18px;
                font-family: Pretendard;
                border: none;
                border-radius: 15px;
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
                border-radius: 15px;
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
    
    font_id = QFontDatabase.addApplicationFont("Pretendard-Regular.otf")
    if font_id == -1:
        print("❌ Pretendard 폰트 로딩 실패")
    else:
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if font_families:
            app.setFont(QFont(font_families[0], 12))
    
    ex = FunctionWindow()
    sys.exit(app.exec_())