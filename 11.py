import re

from flask import Flask, request, jsonify
import os
import time
import fitz  # PyMuPDF
import requests

app = Flask(__name__)


def find_tracking_number(file_path):
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text = page.get_text()
                matches = re.findall(r'\bAP\w+KZ\b', text)
                if matches:
                    return matches[0]
    except Exception as e:
        print(f"Ошибка при открытии и обработке файла: {e}")
    return None


def send_tracking_number_to_server(tracking_number, server_id):
    url = f"http://localhost:3001/orders/{server_id}/trackingNumber"
    payload = {'trackingNumber': tracking_number}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer 56j48P2jHy38uvzrjtFNNkjlwdfkjbvwlkejgbUMqKhTzRjyIRj7xcmChhTYuF1VZuLLcGIsR4egG'
    }
    response = requests.put(url, json=payload, headers=headers)
    return response.text


@app.route('/process_files', methods=['POST'])
def process_files():
    print('start processing files')
    data = request.get_json()
    folder_path = data['folder']
    server_id = data['serverID']
    processed_files = set()
    print(f'start {folder_path} processing {server_id} files')

    if os.path.isdir(folder_path):
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.pdf'):
                file_path = os.path.join(folder_path, file_name)
                if file_path not in processed_files:
                    tracking_number = find_tracking_number(file_path)
                    if tracking_number is not None:
                        response = send_tracking_number_to_server(tracking_number, server_id)
                        processed_files.add(file_path)
                        return jsonify({'message': 'Трек-номер обработан', 'response': response}), 200
        return jsonify({'message': 'Обработка файлов завершена'}), 200
    else:
        return jsonify({'error': 'Указанная папка не найдена'}), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8808)
