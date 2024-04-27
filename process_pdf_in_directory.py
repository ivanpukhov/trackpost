import os
import re

import fitz
import fpdf
import requests


# Convert PDF to high-quality image
def pdf_to_image(file_path, zoom_x=2.0, zoom_y=2.0):
    doc = fitz.open(file_path)
    page = doc[0]
    mat = fitz.Matrix(zoom_x, zoom_y)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img


# Create an image from a long text string
from PIL import Image, ImageDraw, ImageFont


def text_to_image(text):
    width, height = 595, 842  # A4 dimensions in points
    img = Image.new('RGB', (width, height // 2), 'white')
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype('Roboto-Black.ttf', 15)

    y = 10
    x = 10
    max_chars = 40  # Максимальное количество символов на строке
    lines = text.split('\n')
    for line in lines:
        words = line.split(' ')

        new_line = ""
        char_count = 0

        for word in words:
            if char_count + len(word) <= max_chars:
                new_line += word + ' '
                char_count += len(word) + 1  # +1 для пробела
            else:
                d.text((x, y), new_line.rstrip(), font=font, fill=(0, 0, 0))
                y += 20  # Предполагаемая высота строки
                new_line = word + ' '
                char_count = len(word) + 1

        d.text((x, y), new_line.rstrip(), font=font, fill=(0, 0, 0))
        y += 20  # Предполагаемая высота строки

    return img


# Create a new PDF from images
def create_pdf(image1, image2, output_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(image1, x=0, y=0, w=210)
    pdf.image(image2, x=0, y=148.5, w=210)
    pdf.output(output_path)


# Main function
def process_pdf_directory(folder_path, order):
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.pdf'):
            file_path = os.path.join(folder_path, file_name)
            img1 = pdf_to_image(file_path)
            img1 = img1.crop((0, 0, img1.width, img1.height // 2))
            img1.save('img1.png')
            img2 = text_to_image(order)
            img2.save('img2.png')

            # Сохраняем output.pdf в folder_path
            output_path = os.path.join(folder_path, 'output.pdf')
            create_pdf('img1.png', 'img2.png', output_path)


def find_and_copy_words(file_path):
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text = page.get_text()
                matches = re.findall(r'\bAP\w+KZ\b', text)
                if matches:
                    word = matches[0]
                    phone_numbers = re.findall(r'8\(\d{3}\)\d{3}-\d{2}-\d{2}', text)
                    raw_phone = phone_numbers[1] if len(phone_numbers) > 1 else None
                    phone = '7' + ''.join(re.findall(r'\d', raw_phone))[1:] if raw_phone else None
                    return phone, word
    except Exception:
        return phone, word


def send_message(phone, word):
    idInstance = '1101834631'
    apiTokenInstance = 'f0aafa8020394baea4aa3db58aeb2afb02afca8b0e9b4ce4b5'
    url = f"https://api.green-api.com/waInstance{idInstance}/sendMessage/{apiTokenInstance}"
    payload = {"chatId": f"{phone}@c.us", "message": f"Отследить посылочку сможете по треку https://greenman.kz/{word}"}
    headers = {'Content-Type': 'application/json'}
    requests.request("POST", url, headers=headers, json=payload)


def process_pdf_in_directory(folder_path, order):
    processed_files = set()

    for file_name in os.listdir(folder_path):
        if file_name.endswith('.pdf'):
            file_path = os.path.join(folder_path, file_name)
            if file_path not in processed_files:
                phone, word = find_and_copy_words(file_path)
                if phone and word:
                    send_message(phone, word)
                    processed_files.add(file_path)
                    process_pdf_directory(folder_path, order)
                    print('end')
                    break


if __name__ == '__main__':
    folder_path = '/Users/ix/Downloads/'
    process_pdf_in_directory(folder_path)
