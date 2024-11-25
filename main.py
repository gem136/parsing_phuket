import json
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from dateutil.parser import parse
from datetime import timedelta, datetime
import time


class VillaParser:
    def __init__(self, base_url):
        self.base_url = base_url

        # Настройка Selenium WebDriver
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')  # Полезно для правильного отображения элементов
        self.driver = webdriver.Chrome(options=options)

    def parse_villa_links(self, url):
        """Парсит ссылки на виллы с указанной страницы."""
        self.driver.get(url)
        try:
            # Явное ожидание загрузки элементов
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "h2.elementor-heading-title.elementor-size-default > a")
                )
            )
            villa_elements = self.driver.find_elements(By.CSS_SELECTOR, "h2.elementor-heading-title.elementor-size-default > a")
            villa_links = [element.get_attribute("href") for element in villa_elements]
            return villa_links
        except Exception as e:
            print(f"Ошибка при парсинге ссылок с {url}: {e}")
            return []

    def open_villa_links(self, links):
        i = 0
        for url in links:
            try:
                for j in range(2):
                    self.check_total(url,j)
                    print(j)
            except Exception as e:
                # Сохраняем скриншот в случае ошибки
                # self.driver.save_screenshot(f"error_screenshot_{i}.png") #сохранение скриншота ошибки
                i+=1
                print(f"Произошла ошибка на {url}: {e}")

    def parse_all_pages(self):
        """Парсит все страницы и извлекает ссылки на виллы до тех пор, пока не получим пустой список."""
        all_villa_links = []
        page_num = 1

        while True:
            url = f"{self.base_url}{page_num}"
            villa_links = self.parse_villa_links(url)

            if not villa_links:  # Если на странице нет ссылок, выходим из цикла
                print("Больше страниц для парсинга нет.")
                break

            all_villa_links.extend(villa_links)
            print(f"Ссылки с страницы {page_num}: {villa_links}")
            page_num += 1  # Переходим к следующей странице

        return all_villa_links

    def close(self):
        """Закрывает WebDriver."""
        self.driver.quit()

    def check_total(self,url,i):
        self.driver.get(url)
        print(f"Ожидаем доступности первой кнопки на {url}...") #current-post-id
        try:
            # Поиск элемента по XPath
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="current-post-id"]'))
            )
            # Получение текста через JavaScript
            value = self.driver.execute_script("return arguments[0].textContent;", element)
            print("Найденное значение:", value.strip())  # Убираем лишние пробелы
            id = int(value.strip())
        except Exception as e:
            print("Ошибка:", e)
        # Ожидание доступности кнопки
        button = WebDriverWait(self.driver, 3).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".date-container.left"))
        )
        button.click()
        print("Первая кнопка нажата.")
        if i == 1:
            year = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".numInput.cur-year"))
            )
            year.click()

            arrowUp_button = WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".arrowUp"))
            )
            arrowUp_button.click()

        # Попробуем найти элемент с классом 'today'
        today_element = self.driver.find_elements(
            By.XPATH,
            "//span[contains(@class, 'flatpickr-day') and " +
            "contains(@class, 'today') and " +
            "not(contains(@class, 'flatpickr-disabled'))]"
        )
        if today_element:
            print("today element")
            # Извлекаем дату из элемента 'today'
            today_date = today_element[0].get_attribute('aria-label')
            today_date_obj = datetime.strptime(today_date, "%B %d, %Y")
            print(f"Сегодня: {today_date_obj.strftime('%Y-%m-%d')}")

            # Ищем элемент с классом 'available-end' в пределах 7 дней
            available_end_elements = self.driver.find_elements(By.XPATH,
                                                               "//span[contains(@class, 'flatpickr-day') and contains(@class, 'available-end') and not(contains(@class, 'flatpickr-disabled'))]")
            if available_end_elements:
                available_end_date = available_end_elements[0].get_attribute('aria-label')
                available_end_date_obj = datetime.strptime(available_end_date, "%B %d, %Y")
                if (available_end_date_obj - today_date_obj).days <= 7:
                    print("Нажимаем по очереди на кнопки...")
                    first_date_element = today_element
                    first_date_element[0].click()
                    first_date = today_date_obj
                    time.sleep(1)  # Ждем немного между кликами

                    # Нажимаем на вторую дату
                    second_date = available_end_date_obj
                    print(second_date)
                    second_date_element = self.driver.find_element(By.XPATH,
                                                                   f"//span[contains(@aria-label, '{second_date.strftime('%B')}') and contains(@aria-label, '{second_date.day}') and contains(@aria-label, '{second_date.year}')]")
                    second_date_element.click()
                    time.sleep(1)
                else:
                    print(f"Доступность более чем через 7 дней, выбираем через 7 дней.")
                    first_date_element = self.driver.find_elements(By.XPATH,
                                                                   "//span[contains(@class, 'flatpickr-day') and contains(@class, 'today') and not(contains(@class, 'flatpickr-disabled'))]")
                    first_date_element[0].click()
                    future_date = today_date_obj + timedelta(days=7)
                    second_date = future_date
                    month_name = future_date.strftime('%B')  # Название месяца, например, 'December'
                    day = future_date.day  # День месяца, например, '2'
                    year = future_date.year  # Год, например, '2024'

                    # Ищем элемент по части aria-label, содержащей месяц, день и год
                    future_element = self.driver.find_element(By.XPATH,
                                                              f"//span[contains(@aria-label, '{month_name}') and contains(@aria-label, '{day}') and contains(@aria-label, '{year}')]")
                    future_element.click()
                    time.sleep(1)
            else:
                print("Элемент 'available-end' не найден. Конец доступности больше 2 месяцев.")
        else:
            # Если элемента 'today' нет, ищем элемент 'available-start'
            print("not today element")
            available_start_element = self.driver.find_elements(
                By.XPATH,
                "//span[contains(@class, 'flatpickr-day') and contains(@class, 'available-start') and not(contains(@class, 'flatpickr-disabled'))]"
            )
            if available_start_element:
                available_start_date = available_start_element[0].get_attribute('aria-label')
                available_start_date_obj = datetime.strptime(available_start_date, "%B %d, %Y")
                print(f"Начало доступности: {available_start_date_obj.strftime('%Y-%m-%d')}")


                # Ищем элемент с классом 'available-end'
                available_end_element = self.driver.find_elements(By.XPATH,
                                                                  "//span[contains(@class, 'flatpickr-day') and contains(@class, 'available-end') and not(contains(@class, 'flatpickr-disabled'))]")
                if available_end_element:
                    available_end_date = available_end_element[0].get_attribute('aria-label')
                    available_end_date_obj = datetime.strptime(available_end_date, "%B %d, %Y")
                    if (available_end_date_obj - available_start_date_obj).days <= 7:
                        print("Нажимаем по очереди на кнопки...")

                        # Нажимаем на первую дату
                        first_date = available_start_date_obj
                        first_date_element = self.driver.find_element(By.XPATH,
                                                                      f"//span[contains(@aria-label, '{first_date.strftime('%B')}') and contains(@aria-label, '{first_date.day}') and contains(@aria-label, '{first_date.year}')]")

                        first_date_element.click()
                        time.sleep(1)

                        # Нажимаем на вторую дату
                        second_date = first_date + timedelta(days=1)
                        second_date_element = self.driver.find_element(By.XPATH,
                                                                       f"//span[contains(@aria-label, '{second_date.strftime('%B')}') and contains(@aria-label, '{second_date.day}') and contains(@aria-label, '{second_date.year}')]")

                        second_date_element.click()
                        time.sleep(1)
                    else:
                        print(f"Доступность более чем через 7 дней, выбираем через 7 дней.")
                        first_date = available_start_date_obj
                        first_date_element = self.driver.find_element(By.XPATH,
                                                                      f"//span[contains(@aria-label, '{first_date.strftime('%B')}') and contains(@aria-label, '{first_date.day}') and contains(@aria-label, '{first_date.year}')]")

                        first_date_element.click()
                        time.sleep(1)

                        future_date = available_start_date_obj + timedelta(days=7)
                        second_date = future_date
                        month_name = future_date.strftime('%B')  # Название месяца, например, 'December'
                        day = future_date.day  # День месяца, например, '2'
                        year = future_date.year  # Год, например, '2024'

                        # Ищем элемент по части aria-label, содержащей месяц, день и год
                        future_element = self.driver.find_element(By.XPATH,
                                                                  f"//span[contains(@aria-label, '{month_name}') and contains(@aria-label, '{day}') and contains(@aria-label, '{year}')]")

                        future_element.click()
                else:
                    print("Элемент 'available-end' не найден. Конец доступности больше 2 месяцев.")
            else:
                element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".cur-month"))
                )
                month_name = element.text
                available_end_element = self.driver.find_elements(By.XPATH,
                                                                  "//span[contains(@class, 'flatpickr-day') and contains(@class, 'available-end') and not(contains(@class, 'flatpickr-disabled'))]")
                if available_end_element:
                    available_end = available_end_element[0]
                    end_date_label = available_end.get_attribute("aria-label")
                    end_date = datetime.strptime(end_date_label, "%B %d, %Y")

                    # Рассчитываем ближайшую дату
                    target_date = end_date - timedelta(days=7)
                    target_day = target_date.day
                    target_month = target_date.strftime("%B")
                    target_year = target_date.year
                    first_date = target_date
                    second_date = end_date

                    # Ищем future_element и first_element
                    future_element = self.driver.find_element(By.XPATH,
                                                              f"//span[contains(@aria-label, '{target_month}') and contains(@aria-label, '{target_day}') and contains(@aria-label, '{target_year}')]"
                                                              )

                    first_element = self.driver.find_element(By.XPATH,
                                                             f"//span[contains(@aria-label, '{target_month}') and contains(@aria-label, '{target_day}') and contains(@aria-label, '{target_year}')]"
                                                             )

                    # Выводим информацию
                    first_element.click()
                    future_element.click()

                    time.sleep(2)

                else:
                    print("Доступный элемент 'end' не найден.")

                    # Определяем текущий месяц и год
                    now = datetime.now()
                    current_month = now.strftime("%B")
                    current_year = now.year

                    # Задаём два дня: 1 и 8
                    days_to_check = [1, 8]
                    first_date = None
                    second_date = None

                    for i, day in enumerate(days_to_check):
                        print(f"Ищем дату: {day} {current_month} {current_year + 1}")
                        try:
                            # Поиск элемента по XPath
                            element = self.driver.find_element(By.XPATH,
                                                               f"//span[contains(@aria-label, '{current_month}') and contains(@aria-label, '{day}') and contains(@aria-label, '{current_year + 1}')]"
                                                               )
                            element.click()

                            # Сохраняем первую дату
                            if first_date is None:
                                first_date = datetime.strptime(f"{current_month} {day}, {current_year + 1}",
                                                               "%B %d, %Y")
                                print(f"Первая дата сохранена: {first_date}")
                            # Сохраняем вторую дату
                            elif second_date is None:
                                second_date = datetime.strptime(f"{current_month} {day}, {current_year + 1}",
                                                                "%B %d, %Y")
                                print(f"Вторая дата сохранена: {second_date}")
                                break  # Прерываем цикл, если обе даты сохранены

                        except Exception as e:
                            print(f"Элемент для {day} {current_month} {current_year + 1} не найден. Ошибка: {e}")
                    time.sleep(2)
        time.sleep(1)
        try:
            total_price_element = WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="total_price"]'))
            )
            total = total_price_element.get_attribute('textContent').strip()
        except Exception as e:
            print("Total не удалось найти")
            total = "Error"
        try:
            try:
                date = f"{first_date} {second_date}"
            except:
                date = "Error"
            if total and id:
                print(total)
                print(id)
                total = re.sub(r'\s', '', total)
                JsonDump.get_data_and_save(id, date, total)
            else:
                print("Не удалось сохранить")
        except Exception as e:
            print(e)




    def scroll_to_element(self, element):
        """Прокрутка страницы до элемента"""
        self.driver.execute_script("arguments[0].scrollIntoView();", element)


class JsonDump:
    def __init__(self, json_file=f'json_dump_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json'):
        self.json_file = json_file  # Указываем имя файла для сохранения данных

    def save_to_file(self, data):
        try:
            # Открываем файл json_dump.json для чтения
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                existing_data = {"items": []}

            # Добавляем новые данные к уже существующим
            existing_data["items"].extend(data["items"])

            # Записываем обратно в файл
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка при сохранении в файл: {e}")

    def get_data_and_save(self, post_id, date, total):
        data = {"items": []}



        # Добавляем данные в список
        data["items"].append({
            "id": post_id,
            "date": date,
            "total": total
        })

        # Сохраняем данные в json_dump.json
        self.save_to_file(data)


# Пример использования
if __name__ == "__main__":
    base_url = "https://booking.phuket-concierge.com/luxury-villas-in-phuket/?jsf=jet-engine:all-villas&pagenum="
    villa_parser = VillaParser(base_url)
    JsonDump = JsonDump()
    try:
        all_villa_links = villa_parser.parse_all_pages()
        print("Все ссылки на виллы:", all_villa_links)

        villa_parser.open_villa_links(all_villa_links)
    finally:
        villa_parser.close()
