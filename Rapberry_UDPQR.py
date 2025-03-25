import serial
import socket
from PIL import Image, ImageDraw, ImageFont
import qrcode
import time
import tkinter as tk
from threading import Thread

# ====================
# 1. 소켓 및 프린터 초기화
# ====================
UDP_IP = "0.0.0.0"
UDP_PORT = 8888
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

printer_port = "COM16"  # Windows에서 프린터 포트
baud_rate = 9600
# printer_port = "/dev/ttyACM0"  # 라즈베리파이에서 프린터가 연결된 포트
# baud_rate = 19200  # 프린터의 통신 속도

printer = serial.Serial(printer_port, baudrate=baud_rate, timeout=1)

font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

font_small_kr = ImageFont.truetype(font_path, 26)
font_small_en = ImageFont.truetype(font_path, 22)
font_large = ImageFont.truetype(font_path, 30)
font_big = ImageFont.truetype(font_path, 40)

url_mapping = {
            "7c18be3f": "http://192.168.0.100:3000/sketch.html",
            "33f9bd3f": "http://192.168.0.100:3000/button.html",
            "614ebd3f": "http://192.168.0.100:3000/sun.html"
        }

# 한글 폰트 경로 (Nanum Gothic 폰트 설치 필요)
font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

# ====================
# 2. Tkinter UI 설정
# ====================
root = tk.Tk()
root.title("RFID 상태")
root.attributes("-fullscreen", True)

def exit_fullscreen(event):
    root.attributes("-fullscreen", False)

def close_program(event):
    print("프로그램 종료")
    root.destroy()
    printer.close()
    sock.close()

root.bind("<Escape>", exit_fullscreen)
root.bind("<Control-c>", close_program)

status_label = tk.Label(root, text="태그를 인식해주세요", font=("Malgun Gothic", 48), bg="white", fg="black")
status_label.pack(expand=True, fill="both")

# exit_label = tk.Label(root, text="(ESC: 전체 화면 해제, Ctrl+C: 종료)", font=("Arial", 12), bg="white", fg="gray")
# exit_label.pack(side="bottom")

def update_status(message):
    status_label.config(text=message)
    root.update_idletasks()

# ====================
# 3. RFID 처리 함수 (별도 스레드)
# ====================
def rfid_loop():
    try:
        while True:
            update_status("책을 올려주세요")

            print("\n[대기] RFID 데이터를 기다리는 중...")
            data, addr = sock.recvfrom(1024)
            rfid_data = data.decode().strip()
            print(f"[수신됨] RFID: {rfid_data}")

            update_status("인식 중입니다")
            time.sleep(1)

            selected_url = url_mapping.get(rfid_data, "https://www.instagram.com/3dowon/")
            print(f"[URL 선택됨] {selected_url}")

            printer.write(b'\x1b\x40')  # 프린터 초기화

            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(selected_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill="black", back_color="white").convert("1")

            width, height = 580, 1400
            receipt = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(receipt)

            # 헤더 텍스트
            big_text = "P O S T C O D E"
            big_width = draw.textlength(big_text, font=font_big)
            big_x = (width - big_width) // 2
            y = 40

            draw.rectangle([
                (big_x - 30, y - 20),
                (big_x + big_width + 30, y + font_big.size + 20)
            ], fill="black")
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    draw.text((big_x + dx, y + dy), big_text, fill="white", font=font_big)
            y += font_big.size + 40

            # 전시 정보
            title = "3DOWON SOLO EXHIBITION"
            title_x = (width - draw.textlength(title, font=font_large)) // 2
            draw.text((title_x, y), title, fill="black", font=font_large)
            y += 50

            info = [
                ("[장 소] CICA 미술관 3-A 전시실", "[Venue] CICA Museum, Exhibition Room 3-A"),
                ("[날 짜] 2025.03.26 - 2025.03.30", "[Date] 2025.03.26 - 2025.03.30"),
                ("[시 간] 10:30 - 17:30", "[Time] 10:30 AM - 5:30 PM"),
            ]
            for kr, en in info:
                draw.text((10, y), kr, fill="black", font=font_small_kr)
                y += 30
                draw.text((10, y), en, fill="black", font=font_small_en)
                y += 40
            y += 20

            guide = [
                ("* 참여 가이드", "Participation Guide"),
                ("1. Wi-Fi에 연결해주세요.", "Connect to Wi-Fi."),
                ("2. QR 코드를 스캔하여 작품의 세계에 참여하세요.", "Scan the QR code to participate.")
            ]
            for kr, en in guide:
                draw.text((10, y), kr, fill="black", font=font_small_kr)
                y += 30
                draw.text((10, y), en, fill="black", font=font_small_en)
                y += 40
            y += 10

            wifi = ["* Wi-Fi", "SSID: 3DOWON", "P.W: 123456789q"]
            for line in wifi:
                draw.text((10, y), line, fill="black", font=font_small_kr)
                y += 30
            y += 20

            draw.text((10, y), "*참여 QR 코드", fill="black", font=font_small_kr)
            y += 30
            draw.text((10, y), "Participation QR Code", fill="black", font=font_small_en)
            y += 40

            qr_resized = qr_img.resize((int(qr_img.width * 1.8), int(qr_img.height * 1.8)), Image.NEAREST)
            qr_x = (width - qr_resized.width) // 2
            receipt.paste(qr_resized, (qr_x, y))
            y += qr_resized.height + 20

            last_text = "@3dowon"
            last_x = (width - draw.textlength(last_text, font=font_small_kr)) // 2
            draw.text((last_x, y), last_text, fill="black", font=font_small_kr)

            # 프린트 전송
            receipt = receipt.convert("1")
            img_data = bytearray()
            for row in range(receipt.height):
                row_data = bytearray()
                for x in range(0, receipt.width, 8):
                    byte = 0
                    for bit in range(8):
                        if x + bit < receipt.width and receipt.getpixel((x + bit, row)) == 0:
                            byte |= 1 << (7 - bit)
                    row_data.append(byte)
                img_data.extend(row_data)

            bytes_per_row = (receipt.width + 7) // 8
            printer.write(b'\x1d\x76\x30\x00')
            printer.write(bytes([bytes_per_row % 256, bytes_per_row // 256]))
            printer.write(bytes([receipt.height % 256, receipt.height // 256]))
            printer.write(img_data)
            printer.write(b'\x1d\x56\x42\x00')  # 컷

            print("[출력 완료]")
            update_status("영수증을 가져가주세요!")
            time.sleep(2)

    except Exception as e:
        print(f"[오류 발생] {e}")
        update_status("오류가 발생했습니다.")

# ====================
# 4. 메인 실행
# ====================
Thread(target=rfid_loop, daemon=True).start()
root.mainloop()
