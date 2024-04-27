import json
import time

from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

app = Flask(__name__)
CORS(app)

driver = None  # Global driver variable

def setup_selenium():
    global driver

    # Путь к драйверу Selenium Firefox (GeckoDriver)
    driver_path = '/Users/ix/Downloads/geckodriver'

    # Настройка FirefoxOptions для запуска и включение Headless режима
    firefox_options = Options()
    # firefox_options.add_argument('--headless')  # Запуск браузера в безголовом режиме (опционально)

    # Инициализация драйвера
    driver = webdriver.Firefox(service=Service(driver_path), options=firefox_options)


    # Загрузка страницы авторизации
    driver.get('https://post.kz/login')

    # Ввод логина и пароля
    login_field = driver.find_element(By.XPATH, '//*[@id="phone"]')
    login_field.send_keys('7775464450')

    password_field = driver.find_element(By.XPATH, '//*[@id="password"]')
    password_field.send_keys('Pia753!!!')
    time.sleep(1)

    # Нажатие на кнопку входа
    login_button = driver.find_element(By.XPATH, '/html/body/div/div[3]/div/div/div[2]/form/div[3]/button')
    login_button.click()

    # Ожиданиеz
    time.sleep(1)

    # Перейти на страницу https://post.kz/prefills/package
    driver.get('https://post.kz/prefills/package')


def load_data():
    with open('data.json', 'r') as file:
        data = json.load(file)
    return data


def find_closest(input_value, data):
    if not input_value:
        return None, None  # Возвращаем None, если input_value пустое

    closest_key = None
    closest_city_name = None
    closest_distance = None

    for key, cities in data.items():
        for city in cities:
            index = city['index']
            distance = abs(int(input_value) - int(index))

            # Теперь мы выбираем ближайшее меньшее или равное значение, вместо просто ближайшего
            if closest_distance is None or distance < closest_distance or (distance == closest_distance and int(index) <= int(input_value)):
                closest_distance = distance
                closest_key = key
                closest_city_name = city['city']

    return closest_key, closest_city_name


setup_selenium()  # Call the setup function before starting the Flask app


@app.route('/process', methods=['POST'])
def process():
    global driver

    data = request.get_json()

    # Вместо запроса ввода данных используем данные из POST запроса
    kot = data.get('kot', '')
    user_input = data.get('user_input', '')
    street = data.get('street', '')
    number = data.get('number', '')
    print(kot)
    print(user_input)
    print(street)
    print(number)
    # Ожидание загрузки страницы
    time.sleep(1)

    # Нажать на //*[@id="kzp"]/div[3]/div/main/div/div[2]/ul/li[1]
    first_button = driver.find_element(By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/ul/li[1]')
    first_button.click()

    # Подождать 0.1 секунду и нажать на //*[@id="kzp"]/div[3]/div/main/div/div[2]/ul/li[2]
    time.sleep(0.1)
    second_button = driver.find_element(By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/ul/li[2]')
    second_button.click()

    # Ввод имени
    input_field_kot = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/form[2]/div[1]/input')))
    input_field_kot.send_keys(kot)

    # Нажатие на чекбокс
    checkbox = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/form[2]/div[3]/div[1]/label[2]')))
    driver.execute_script("arguments[0].click();", checkbox)

    # Загрузка данных и поиск ближайшего значения
    data = load_data()
    closest_key, closest_city_name = find_closest(user_input, data)

    # Проверка, не являются ли closest_key и closest_city_name None
    if closest_key is None or closest_city_name is None:
        return jsonify({'status': 'error', 'message': 'Invalid input_value'}), 400

    # Выбор региона и города из выпадающих списков
    region_select = Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/form[2]/div[3]/div[2]/div[1]/select'))))
    region_select.select_by_value(closest_key)

    city_select = Select(WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/form[2]/div[3]/div[2]/div[2]/select'))))
    city_select.select_by_visible_text(closest_city_name)

    # Очистка и ввод значения индекса
    input_field_index = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/form[2]/div[3]/div[2]/div[3]/input')))
    driver.execute_script("arguments[0].scrollIntoView();", input_field_index)
    input_field_index.clear()
    input_field_index.send_keys(user_input)

    # Ввод адреса
    house = street.split()[-1]
    street = " ".join(street.split()[:-1])

    input_field_street = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/form[2]/div[3]/div[2]/div[4]/input')))
    input_field_street.send_keys(street)

    input_field_house = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/form[2]/div[3]/div[2]/div[5]/input')))
    input_field_house.send_keys(house)

    # Ввод номера телефона
    input_field_number = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, '/html/body/div/div[3]/div/main/div/div[2]/div[1]/form[2]/div[2]/input')))
    input_field_number.send_keys(number)
    time.sleep(2)  # Дополнительная задержка для завершения операции

    # Нажатие на кнопку
    submit_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/div/button')))
    driver.execute_script("arguments[0].scrollIntoView();", submit_button)
    driver.execute_script("arguments[0].click();", submit_button)
    time.sleep(2)  # Дополнительная задержка для завершения операции

    # Нажатие на вторую кнопку
    final_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="kzp"]/div[3]/div/main/div/div[2]/div[1]/div/div/button')))
    driver.execute_script("arguments[0].scrollIntoView();", final_button)
    driver.execute_script("arguments[0].click();", final_button)

    # Ожидание завершения процесса
    time.sleep(2)

    # Сохранение страницы
    driver.save_screenshot("final_page.png")

    return jsonify({'status': 'success', 'message': 'Operation completed successfully'}), 200


if __name__ == "__main__":
    app.run(debug=True)
