from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver

options = FirefoxOptions()
driver = webdriver.Remote(options=options, command_executor="http://localhost:4444")
driver.get("https://selenium.dev")
driver.quit()