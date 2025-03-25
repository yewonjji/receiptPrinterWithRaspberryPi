import serial
import socket
from PIL import Image, ImageDraw, ImageFont
import qrcode
import time

# ====================
# 1. 소켓 및 프린터 초기화
# ====================
UDP_IP = "0.0.0.0"
UDP_PORT = 8888
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

printer_port = "COM16"  # Windows에서 프린터 포트
baud_rate = 9600
printer = serial.Serial(printer_port, baudrate=baud_rate, timeout=1)

font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

font_small_kr = ImageFont.truetype(font_path, 26)
font_small_en = ImageFont.truetype(font_path, 22)
font_large = ImageFont.truetype(font_path, 30)
font_big = ImageFont.truetype(font_path, 40)

# ====================
# 2. RFID 무한 수신 및 프린트 루프
# ====================
try:
    while True:
        print("\n[대기] RFID 데이터를 기다리는 중...")
        data, addr = sock.recvfrom(1024)
        rfid_data = data.decode().strip()
        print(f"[수신됨] RFID: {rfid_data}")

        # RFID -> URL 매핑
        url_mapping = {
            "7c18be3f": "http://192.168.0.100:3000/sketch.html",
            "33f9bd3f": "http://192.168.0.100:3000/button.html",
            "614ebd3f": "http://192.168.0.100:3000/sun.html"
        }
        selected_url = url_mapping.get(rfid_data, "https://www.instagram.com/3dowon/")
        print(f"[URL 선택됨] {selected_url}")

        # 프린터 초기화
        printer.write(b'\x1b\x40')

        # QR 생성
        participation_qr = qrcode.QRCode(box_size=6, border=2)
        participation_qr.add_data(selected_url)
        participation_qr.make(fit=True)
        participation_qr_img = participation_qr.make_image(fill="black", back_color="white").convert("1")

        # 영수증 이미지 생성
        width, height = 580, 1400
        receipt_img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(receipt_img)

        # 헤더
        big_text = "P O S T C O D E"
        big_text_width = draw.textlength(big_text, font=font_big)
        big_text_x = (width - big_text_width) // 2
        current_y = 40

        draw.rectangle([
            (big_text_x - 30, current_y - 20),
            (big_text_x + big_text_width + 30, current_y + font_big.size + 20)
        ], fill="black")

        for dx in range(-2, 3):
            for dy in range(-2, 3):
                draw.text((big_text_x + dx, current_y + dy), big_text, fill="white", font=font_big)
        current_y += font_big.size + 40

        # 전시 타이틀
        title_text = "3DOWON SOLO EXHIBITION"
        title_width = draw.textlength(title_text, font=font_large)
        title_x = (width - title_width) // 2
        draw.text((title_x, current_y), title_text, fill="black", font=font_large)
        current_y += 50

        # 전시 정보
        info_text = [
            ("[장 소] CICA 미술관 3-A 전시실", "[Venue] CICA Museum, Exhibition Room 3-A"),
            ("[날 짜] 2025.03.26 - 2025.03.30", "[Date] 2025.03.26 - 2025.03.30"),
            ("[시 간] 10:30 - 17:30", "[Time] 10:30 AM - 5:30 PM"),
        ]
        for kr, en in info_text:
            draw.text((10, current_y), kr, fill="black", font=font_small_kr)
            current_y += 30
            draw.text((10, current_y), en, fill="black", font=font_small_en)
            current_y += 40

        current_y += 20

        # 참여 가이드
        guide_text = [
            ("* 참여 가이드", "Participation Guide"),
            ("1. Wi-Fi에 연결해주세요.", "Connect to Wi-Fi."),
            ("2. QR 코드를 스캔하여 작품의 세계에 참여하세요.", "Scan the QR code to participate."),
        ]
        for kr, en in guide_text:
            draw.text((10, current_y), kr, fill="black", font=font_small_kr)
            current_y += 30
            draw.text((10, current_y), en, fill="black", font=font_small_en)
            current_y += 40

        current_y += 10

        # Wi-Fi 정보
        wifi_info = [
            "* Wi-Fi",
            "SSID: 3DOWON",
            "P.W: 123456789q",
        ]
        for line in wifi_info:
            draw.text((10, current_y), line, fill="black", font=font_small_kr)
            current_y += 30

        current_y += 20

        # QR 코드 안내
        draw.text((10, current_y), "*참여 QR 코드", fill="black", font=font_small_kr)
        current_y += 30
        draw.text((10, current_y), "Participation QR Code", fill="black", font=font_small_en)
        current_y += 40

        # QR 코드 삽입
        qr_scale = 1.35
        qr_width, qr_height = participation_qr_img.size
        new_qr_size = (int(qr_width * qr_scale), int(qr_height * qr_scale))
        participation_qr_img_resized = participation_qr_img.resize(new_qr_size, Image.NEAREST)
        qr_x = (width - participation_qr_img_resized.size[0]) // 2
        receipt_img.paste(participation_qr_img_resized, (qr_x, current_y))
        current_y += participation_qr_img_resized.size[1] + 20

        # 마지막 문구
        final_text = "@3dowon"
        final_text_width = draw.textlength(final_text, font=font_small_kr)
        final_x = (width - final_text_width) // 2
        draw.text((final_x, current_y), final_text, fill="black", font=font_small_kr)

        # 이미지 프린트용 1비트 변환
        receipt_img = receipt_img.convert("1")

        # 이미지 데이터를 프린터로 전송
        width, height = receipt_img.size
        bytes_per_row = (width + 7) // 8
        image_data = bytearray()

        for y in range(height):
            row = bytearray()
            for x in range(0, width, 8):
                byte = 0
                for bit in range(8):
                    if x + bit < width and receipt_img.getpixel((x + bit, y)) == 0:
                        byte |= 1 << (7 - bit)
                row.append(byte)
            image_data.extend(row)

        printer.write(b'\x1d\x76\x30\x00')
        printer.write(bytes([bytes_per_row % 256, bytes_per_row // 256]))
        printer.write(bytes([height % 256, height // 256]))
        printer.write(image_data)
        printer.write(b'\x1d\x56\x42\x00')  # 컷 명령

        print("[출력 완료] 프린터로 출력됨.\n")

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n[종료] 프로그램을 종료합니다.")
    printer.close()
    sock.close()
