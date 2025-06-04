import os
import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QStackedWidget
from PyQt5.QtGui import QFontDatabase, QFont

from intro_window import IntroWindow
from function_window import FunctionWindow
from select_window import SelectionWindow

def launch_masking_script():
    python_executable = sys.executable
    script_path = os.path.join(os.path.dirname(__file__), "text_masking.py")

    if not os.path.exists(script_path):
        print("❌ text_masking.py 파일이 존재하지 않습니다:", script_path)
        return

    print("🚀 text_masking.py 실행 시작!")

    subprocess.Popen(
        [python_executable, script_path],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

class MainWindow(QStackedWidget):
    def __init__(self):
        super().__init__()

        self.intro = IntroWindow(self.route_from_intro)
        self.selection = SelectionWindow(self.show_function_screen)
        self.function = FunctionWindow(self.back_to_selection)

        self.addWidget(self.intro)      # 0
        self.addWidget(self.selection)  # 1
        self.addWidget(self.function)   # 2

        self.setWindowTitle("Erase Me")
        self.resize(1000, 700)

        # 인트로 → 선택 or 기능 자동 분기
        self.setCurrentIndex(0)
        self.show()

    def route_from_intro(self):
        if os.path.exists("selected_fields.json"):
            self.show_function_screen()
        else:
            self.setCurrentIndex(1)

    def show_function_screen(self):
        self.function.reload_selected_fields()
        self.setCurrentIndex(2)

    def back_to_selection(self):
        if os.path.exists("selected_fields.json"):
            os.remove("selected_fields.json")
        self.setCurrentIndex(1)


if __name__ == '__main__':
    launch_masking_script()

    app = QApplication(sys.argv)

    # Pretendard 폰트 로드
    font_id = QFontDatabase.addApplicationFont("Pretendard-Regular.otf")
    if font_id != -1:
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            app.setFont(QFont(families[0], 12))

    win = MainWindow()
    sys.exit(app.exec_())
