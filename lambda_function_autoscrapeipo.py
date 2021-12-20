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
    month = date.month
    date = datetime.datetime.now()
    year = date.year
    day = date.day
    today = '{}{}{}'.format(year,month,day)
    

    driver.get('https://www.rakuten-sec.co.jp/web/foreign/us/ipo/future/')
    
    tickerTr = driver.find_element(By.XPATH, '//*[@id="data-json-ipo-main"]/table/tbody').find_elements(By.TAG_NAME, "tr")
    
    print(len(tickerTr))
    
    list = []
    
    for i in range(0, len(tickerTr)):
            # 決済予定のTicker情報の行(不要なもの含む)
            tickerTd = tickerTr[i].find_elements(By.TAG_NAME, "td")
            # IPO予定日抜き出し
            a = tickerTd[4].text.split('/')
            settleday = '{}/{}/{}'.format(a[2], a[0], a[1])
            # ティッカー抜き出し
            ticker = '${}'.format(tickerTd[0].text)
            if int(a[0]) < month:
                break
            list.append('{} {}\n'.format(settleday, ticker))
            
    print(list)    
    
    bucket_name = 'ipo-list-for-blog'
    file_key = 'ipo_{}{}{}.txt'.format(year,month,day)
    file_path = '/tmp/{}'.format(file_key)
    
    f = open('/tmp/{}'.format(file_key), 'w')
    f.writelines(list)
    f.close
    
    with open('/tmp/{}'.format(file_key)) as f:
        s = f.read()
        print(type(s))
        print(s)
        f.close
    
    s3 = boto3.resource('s3')
    s3.Bucket(bucket_name).upload_file(Filename=file_path, Key=file_key)
    
    time.sleep(10)
    driver.quit()
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }