from selenium.webdriver import Chrome, ChromeOptions

options = ChromeOptions()
options.add_argument('--proxy-server=socks5://127.0.0.1:9090')

driver = Chrome('./chromedriver.exe', options=options)
driver_mics = Chrome('./chromedriver.exe')

driver.set_window_rect(3920, 0, 850, 1000)
driver_mics.set_window_rect(4790, 0, 1100, 1000)