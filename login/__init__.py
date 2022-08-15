from selenium.webdriver import Chrome

driver = Chrome('./chromedriver.exe')
driver_mics = Chrome('./chromedriver.exe')

driver.set_window_rect(1920, 0, 850, 1000)
driver_mics.set_window_rect(2790, 0, 1100, 1000)