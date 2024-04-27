import json
import os
import time

import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

app = Flask(__name__)
CORS(app)


def setup_selenium():
    driver_path = '/Users/ix/Downloads/geckodriver'
    timestamp = str(int(time.time()))
    download_folder = f'/Users/ix/Desktop/post/{timestamp}'
    os.makedirs(download_folder, exist_ok=True)  # Создаем папку, если она еще не существует

    firefox_options = Options()
    firefox_options.set_preference("browser.download.folderList", 2)
    firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
    firefox_options.set_preference("browser.download.dir", download_folder)
    firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")  # MIME типы

    driver = webdriver.Firefox(service=Service(driver_path), options=firefox_options)
    driver.get('https://post.kz/login')
    login_field = driver.find_element(By.XPATH, '//*[@id="phone"]')
    login_field.send_keys('7775464450')
    password_field = driver.find_element(By.XPATH, '//*[@id="password"]')
    password_field.send_keys('Pia753!!!')
    time.sleep(5)
    login_button = driver.find_element(By.XPATH, '/html/body/div/div[3]/div/div/div[2]/form/div[3]/button')
    login_button.click()
    time.sleep(5)
    driver.get('https://post.kz/prefills/package')
    return driver, download_folder


def load_data():
    with open('data.json', 'r') as file:
        data = json.load(file)
    return data


def send_data_to_8808(folder_path, server_id):
    url = 'http://localhost:8808/process_files'
    data = {
        'folder': folder_path,
        'serverID': server_id
    }

    headers = {'Content-Type': 'application/json'}
    print(f"Sending POST request to {url} with data: {data}")
    response = requests.post(url, json=data, headers=headers)
    print(f"Received response: {response.status_code} - {response.text}")
    return response.json()


def find_closest(input_value, data):
    if not input_value:
        return None, None
    closest_key = None
    closest_city_name = None
    closest_distance = None
    for key, cities in data.items():
        for city in cities:
            index = city['index']
            distance = abs(int(input_value) - int(index))
            if closest_distance is None or distance < closest_distance or (
                    distance == closest_distance and int(index) <= int(input_value)):
                closest_distance = distance
                closest_key = key
                closest_city_name = city['city']
    return closest_key, closest_city_name


@app.route('/process', methods=['POST'])
def process():
    max_attempts = 3  # Максимальное количество попыток
    attempts = 0

    while attempts < max_attempts:
        try:
            driver, download_folder = setup_selenium()

            data = request.get_json()
            kot = data.get('kot', '')
            user_input = data.get('user_input', '')
            street = data.get('street', '')
            number = data.get('number', '')
            serverId = data.get('serverId', '')
            time.sleep(3)

            first_button = driver.find_element(By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/ul/li[1]')
            first_button.click()
            time.sleep(1)
            second_button = driver.find_element(By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/ul/li[2]')
            second_button.click()
            # Нажать на //*[@id="kzp"]/div[3]/div/main/div/div[2]/ul/li[1]
            first_button = driver.find_element(By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/ul/li[1]')
            first_button.click()

            # Подождать 0.1 секунду и нажать на //*[@id="kzp"]/div[3]/div/main/div/div[2]/ul/li[2]
            time.sleep(0.1)
            second_button = driver.find_element(By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/ul/li[2]')
            second_button.click()

            input_field_kot = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/form[2]/div[1]/input')))
            input_field_kot.send_keys(kot)
            checkbox = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/form[2]/div[3]/div[1]/label[2]')))
            driver.execute_script("arguments[0].click();", checkbox)
            data = load_data()
            closest_key, closest_city_name = find_closest(user_input, data)
            if closest_key is None or closest_city_name is None:
                driver.quit()
                return jsonify({'status': 'error', 'message': 'Invalid input_value'}), 400
            region_select = Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/form[2]/div[3]/div[2]/div[1]/select'))))
            region_select.select_by_value(closest_key)
            city_select = Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/form[2]/div[3]/div[2]/div[2]/select'))))
            city_select.select_by_visible_text(closest_city_name)
            input_field_index = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/form[2]/div[3]/div[2]/div[3]/input')))
            driver.execute_script("arguments[0].scrollIntoView();", input_field_index)
            input_field_index.clear()
            input_field_index.send_keys(user_input)
            house = street.split()[-1]
            street = " ".join(street.split()[:-1])
            input_field_street = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/form[2]/div[3]/div[2]/div[4]/input')))
            input_field_street.send_keys(street)
            input_field_house = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/form[2]/div[3]/div[2]/div[5]/input')))
            input_field_house.send_keys(house)
            input_field_number = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, '/html/body/div/div[3]/div/main/div/div[2]/div[1]/form[2]/div[2]/input')))
            input_field_number.send_keys(number)
            time.sleep(2)
            submit_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/div/button')))
            driver.execute_script("arguments[0].scrollIntoView();", submit_button)
            driver.execute_script("arguments[0].click();", submit_button)
            time.sleep(2)
            final_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/div/div/button')))
            driver.execute_script("arguments[0].scrollIntoView();", final_button)
            driver.execute_script("arguments[0].click();", final_button)
            time.sleep(20)
            response_8808 = send_data_to_8808(download_folder, serverId)

            driver.quit()
            return jsonify(
                {'status': 'success', 'message': 'Operation completed successfully', 'folder': download_folder,
                 'serverID': serverId, 'response_8808': response_8808}), 200
        except Exception as e:
            driver.quit()
            attempts += 1  # Увеличиваем счетчик попыток
            if attempts == max_attempts:
                return jsonify({'status': 'error', 'message': 'Failed after several attempts: ' + str(e)}), 500
            time.sleep(5)  # Небольшая задержка перед следующей попыткой


if __name__ == "__main__":
    app.run(debug=True)
