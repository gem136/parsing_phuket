from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime, timedelta

# Получаем текущее время в формате "YYYY-MM-DD_HH-MM-SS"
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Выводим сформированное время
print(current_time)