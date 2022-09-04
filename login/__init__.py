from selenium.webdriver import Chrome, ChromeOptions


options = ChromeOptions()
options.add_argument('--proxy-server=socks5://127.0.0.1:9090')

driver = Chrome('./chromedriver.exe', options=options)
driver_mics = Chrome('./chromedriver.exe')