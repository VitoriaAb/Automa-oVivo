from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time  # Importe a biblioteca time

# O ChromeDriverManager vai baixar e gerenciar o chromedriver para você.
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Agora você pode usar o driver para sua automação
driver.get("https://www.google.com")

# O comando time.sleep(10) fará com que a janela do navegador permaneça aberta por 10 segundos
time.sleep(10)

# O script termina e o navegador é fechado automaticamente