from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime, timedelta

# Инициализация драйвера
driver = webdriver.Chrome()


def parse_villa_links(url):
    """Парсит ссылки на виллы с указанной страницы."""
    driver.get(url)
    try:
        # Явное ожидание загрузки элементов
        WebDriverWait(driver, 3).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "h2.elementor-heading-title.elementor-size-default > a")
            )
        )
        villa_elements = driver.find_elements(By.CSS_SELECTOR,
                                                   "h2.elementor-heading-title.elementor-size-default > a")
        villa_links = [element.get_attribute("href") for element in villa_elements]
        return villa_links
    except Exception as e:
        print(f"Ошибка при парсинге ссылок с {url}: {e}")
        return []

def parse_all_pages():
    """Парсит все страницы и извлекает ссылки на виллы до тех пор, пока не получим пустой список."""
    all_villa_links = []
    page_num = 1
    base_url ="https://booking.phuket-concierge.com/luxury-villas-in-phuket/?jsf=jet-engine:all-villas&pagenum="

    while True:
        url = f"{base_url}{page_num}"
        villa_links = parse_villa_links(url)

        if not villa_links:  # Если на странице нет ссылок, выходим из цикла
            print("Больше страниц для парсинга нет.")
            break

        all_villa_links.extend(villa_links)
        print(f"Ссылки с страницы {page_num}: {villa_links}")
        page_num += 1  # Переходим к следующей странице

    return all_villa_links

driver.get('https://booking.phuket-concierge.com/product/baan-taley-rom/')
# Ожидание доступности кнопки
button = WebDriverWait(driver, 20).until(
    EC.visibility_of_element_located((By.CSS_SELECTOR, ".date-container.left"))
)
button.click()

year = WebDriverWait(driver, 20).until(
    EC.visibility_of_element_located((By.CSS_SELECTOR, ".numInput.cur-year"))
)
year.click()

arrowUp_button = WebDriverWait(driver, 20).until(
    EC.visibility_of_element_located((By.CSS_SELECTOR, ".arrowUp"))
)
arrowUp_button.click()
time.sleep(10)
driver.quit()