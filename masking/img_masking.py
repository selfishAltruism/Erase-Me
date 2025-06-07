import os
import time
import requests
from PIL import ImageGrab
from dotenv import load_dotenv

def main():
    load_dotenv()

    IMG_MASKING_SERVER_URL = os.getenv("IMG_MASKING_SERVER_URL")
    if not IMG_MASKING_SERVER_URL:
        print("❌ IMG_MASKING_SERVER_URL 환경 변수가 설정되지 않았습니다.")
        return

    print("🚧 이미지 클립보드 감시 중...")

    last_clip = None

    while True:
        img = ImageGrab.grabclipboard()
        if img is not None and img != last_clip:
            last_clip = img
            img_path = "img/code.png"
            os.makedirs("img", exist_ok=True)
            img.save(img_path)
            print(f"✅ 캡처 이미지 저장됨: {img_path}")

            # 서버로 업로드: 블로킹
            try:
                with open(img_path, "rb") as f:
                    print("📡 서버로 업로드 중...")
                    res = requests.post(
                        IMG_MASKING_SERVER_URL,
                        files={"image": f}
                    )
                if res.status_code == 200:
                    with open("masked_result.png", "wb") as out:
                        out.write(res.content)
                    print("🎉 마스킹된 이미지 저장됨: masked_result.png")
                else:
                    print(f"❌ 서버 오류: {res.status_code}")
            except Exception as e:
                print(f"❌ 요청 실패: {e}")

        time.sleep(0.5)  # 주기적 감시 (0.5초마다)

if __name__ == "__main__":
    main()
