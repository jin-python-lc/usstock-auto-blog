import json
from selenium import webdriver
from selenium.webdriver.common.by import By
import time 
import datetime
import boto3


def headless_chrome():
   options = webdriver.ChromeOptions()
   options.binary_location = "/opt/headless/python/bin/headless-chromium"
   options.add_argument("--headless")
   options.add_argument("--no-sandbox")
   options.add_argument("--single-process")
   options.add_argument("--disable-gpu")
   options.add_argument("--window-size=1280x1696")
   options.add_argument("--disable-application-cache")
   options.add_argument("--disable-infobars")
   options.add_argument("--hide-scrollbars")
   options.add_argument("--enable-logging")
   options.add_argument("--log-level=0")
   options.add_argument("--ignore-certificate-errors")
   options.add_argument("--homedir=/tmp")

   driver = webdriver.Chrome(
       executable_path="/opt/headless/python/bin/chromedriver",
       chrome_options=options
   )
   return driver



driver = headless_chrome()

def lambda_handler(event, context):
    
    date = datetime.datetime.now()
    print(date)
    year = date.year
    m = date.month
    day = date.day
    print(year,m,day)
    today = '{}{}{}'.format(year,m,day)
    print(today)
    
    # クリック関数
    def click(xpath):
        time.sleep(1)
        xpath = driver.find_element_by_xpath('{}'.format(xpath))
        xpath.click()
    
    # 入力関数
    def sendKeys(xpath, key):
        time.sleep(1)
        xpath = driver.find_element_by_xpath('{}'.format(xpath))
        xpath.send_keys('{}'.format(key))
    
    # 入力関数(+clear)
    def clear_sendKeys(xpath, key):
        time.sleep(1)
        xpath = driver.find_element_by_xpath('{}'.format(xpath))
        xpath.clear()
        xpath.send_keys('{}'.format(key))
        
    
    driver.get('https://site0.sbisec.co.jp/marble/market/calendar/schedule/foreign.do?Param6=US')
    
    # cronだから1日だが
    click('//*[@id="col_{}"]'.format(today))
    
    # カレンダーからエレメント取得
    elements = driver.find_elements(By.CLASS_NAME, 'md-td-01')
    # 最初2つ要らない要素あるから消す
    del elements[0:2]
    
    # テキスト書き出し用リスト
    list = []
    
    # 日毎エレメントリスト文繰り返し
    for i in range(0, len(elements)):
        time.sleep(1)
        elements[i].click()
        
        #　表示数50に変更
        click('//*[@id="page_rows_select"]')
        click('//*[@id="page_rows_select"]/option[5]')
    
        # その日決済予定の企業全て
        tickerTr = driver.find_element(By.XPATH, '//*[@id="info_table"]/table/tbody').find_elements(By.TAG_NAME, "tr")
        
        for d in range(0, len(tickerTr)):
            # 決済予定のTicker情報の行(不要なもの含む)
            tickerTd = tickerTr[d].find_elements(By.TAG_NAME, "td")
            # 決算予定日抜き出し
            settleday = tickerTd[0].text
            # ティッカー抜き出し
            ticker = '${}'.format(tickerTd[2].text)
            list.append('{} {}\n'.format(settleday, ticker))
    
    
    bucket_name = 'ticker-list-for-blog'
    file_key = '{}{}{}.txt'.format(year,m,day)
    file_path = '/tmp/{}'.format(file_key)
    
    f = open('/tmp/{}'.format(file_key), 'w')
    f.writelines(list)
    f.close
    
    s3 = boto3.resource('s3')
    s3.Bucket(bucket_name).upload_file(Filename=file_path, Key=file_key)
    
    time.sleep(10)
    driver.quit()
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
