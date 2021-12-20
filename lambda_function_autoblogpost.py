from logging import basicConfig, captureWarnings
from selenium import webdriver
from selenium.webdriver.common.by import By
import time 
from datetime import datetime
from botocore.vendored import requests
from urllib.parse import urljoin
import os
import json
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
    #####今日の日付取得
    date = datetime.now()
    year = date.year
    month = date.month
    day = date.day
    today = '{}/{}/{}'.format(year,month,day)
    tommorow = '{}/{}/{}'.format(year,month,day+1)###################
    print(today)
    print(tommorow)
    
    
    
    s3 = boto3.client('s3')
    bucket_name = '*****'
    file_name = '*****.txt' 
    response = s3.get_object(Bucket=bucket_name, Key=file_name)
    body = response['Body'].read()
    bodystr = body.decode('utf-8')
    lines = bodystr.splitlines()
    print(lines)
    
    tickers = []
    for i in range(0, len(lines)):
        if lines[i].split()[0] == tommorow:
            tickers.append([lines[i].split()[1][1:]])
            print('matched',lines[i] )
        else:
            print('notmatch', lines[i])
    print(tickers)
    
    #####検索ボリューム
    
    dict1 = {}
    for i in range(0, len(tickers)):
        time.sleep(2)
        driver.get('https://aramakijake.jp/keyword/index.php?keyword={}'.format(tickers[i][0]))
        elements = driver.find_elements(By.CLASS_NAME, 'sp_type')
        #tickers[i].append(int(elements[1].text.replace(',', '')))
        print(tickers[i][0])
        print(elements[1])
        if len(elements) > 1:
            dict1['{}'.format(tickers[i][0])] = int(elements[1].text.replace(',', ''))
    
    # 検索ボリューム多い順
    dict2 = sorted(dict1.items(), key=lambda x:x[1], reverse=True)[:3]
    print(dict2)
    
    
    def txt(xpath):
        text = driver.find_element_by_xpath('{}'.format(xpath)).text
        return text
    
    # 企業情報まとめ
    stockInformation = []
    stockYoy = []
    stockPreRev = []
    
    ##### 情報取得 about
    for i in range(0, len(dict2)):
        time.sleep(2)
        driver.get('https://stocks.finance.yahoo.co.jp/us/profile/{}'.format(dict2[i][0]))
        #
        about = txt('//*[@id="main"]/div[4]/div/table/tbody/tr[1]/td')
        loanch = txt('//*[@id="main"]/div[4]/div/table/tbody/tr[5]/td')
        category = txt('//*[@id="main"]/div[4]/div/table/tbody/tr[7]/td')
        market = txt('//*[@id="main"]/div[4]/div/table/tbody/tr[8]/td')
        enployee = txt('//*[@id="main"]/div[4]/div/table/tbody/tr[9]/td')
        site = txt('//*[@id="main"]/div[4]/div/table/tbody/tr[10]/td')
        stockInformation.append([dict2[i][0], about, loanch, category, market, enployee, site])
    
    print(stockInformation)
    
    ##### 情報取得 eps, revenew, yoy
    for i in range(0, len(dict2)):
        time.sleep(2)
        driver.get('https://finance.yahoo.com/quote/{}/analysis'.format(dict2[i][0]))
        est_eps = txt('//*[@id="Col1-0-AnalystLeafPage-Proxy"]/section/table[1]/tbody/tr[2]/td[2]/span')
        est_rev = txt('//*[@id="Col1-0-AnalystLeafPage-Proxy"]/section/table[2]/tbody/tr[2]/td[2]/span')
        time.sleep(2)
        driver.get('https://finance.yahoo.com/quote/{}/key-statistics'.format(dict2[i][0]))
        prev_yoy = txt('//*[@id="Col1-0-KeyStatistics-Proxy"]/section/div[2]/div[3]/div/div[4]/div/div/table/tbody/tr[3]/td[2]')
        stockYoy.append([dict2[i][0], est_eps, est_rev, prev_yoy])
    
    print(stockYoy)
    
    ##### 情報取得 previewsly revenew
    for i in range(0, len(dict2)):
        time.sleep(2)
        driver.get('https://finance.yahoo.com/quote/{}/financials'.format(dict2[i][0]))
        #
        con = len(driver.find_elements_by_xpath('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/*'))-1
        print(con)
        #
        #
        if con >= 5:
            ttm = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[2]')
            pre = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[3]')
            pre1 = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[4]')
            pre2 = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[5]')
            pre3 = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[6]')
            #
            ttm_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[2]').replace(',', ''))*1000)
            pre_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[3]').replace(',', ''))*1000)
            pre1_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[4]').replace(',', ''))*1000)
            pre2_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[5]').replace(',', ''))*1000)
            pre3_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[6]').replace(',', ''))*1000)
            #
            ttmg_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[2]').replace(',', ''))*1000)
            preg_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[3]').replace(',', ''))*1000)
            pre1g_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[4]').replace(',', ''))*1000)
            pre2g_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[5]').replace(',', ''))*1000)
            pre3g_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[6]').replace(',', ''))*1000)
            stockPreRev.append([dict2[i][0], [ttm,ttm_v,ttmg_v], [pre,pre_v,preg_v], [pre1,pre1_v,pre1g_v], [pre2,pre2_v,pre1g_v], [pre3,pre3_v,pre1g_v]])
        elif con == 4:
            ttm = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[2]')
            pre = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[3]')
            pre1 = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[4]')
            pre2 = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[5]')
            #
            ttm_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[2]').replace(',', ''))*1000)
            pre_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[3]').replace(',', ''))*1000)
            pre1_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[4]').replace(',', ''))*1000)
            pre2_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[5]').replace(',', ''))*1000)
            #
            ttmg_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[2]').replace(',', ''))*1000)
            preg_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[3]').replace(',', ''))*1000)
            pre1g_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[4]').replace(',', ''))*1000)
            pre2g_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[5]').replace(',', ''))*1000)
            stockPreRev.append([dict2[i][0], [ttm,ttm_v,ttmg_v], [pre,pre_v,preg_v], [pre1,pre1_v,pre1g_v], [pre2,pre2_v,pre1g_v]])
        elif con == 3:
            ttm = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[2]')
            pre = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[3]')
            pre1 = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[4]')
            #
            ttm_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[2]').replace(',', ''))*1000)
            pre_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[3]').replace(',', ''))*1000)
            pre1_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[4]').replace(',', ''))*1000)
            #
            ttmg_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[2]').replace(',', ''))*1000)
            preg_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[3]').replace(',', ''))*1000)
            pre1g_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[4]').replace(',', ''))*1000)
            stockPreRev.append([dict2[i][0], [ttm,ttm_v,ttmg_v], [pre,pre_v,preg_v], [pre1,pre1_v,pre1g_v]])
        elif con == 2:
            ttm = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[2]')
            pre = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[3]')
            #
            ttm_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[2]').replace(',', ''))*1000)
            pre_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[3]').replace(',', ''))*1000)
            #
            ttmg_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[2]').replace(',', ''))*1000)
            preg_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[3]').replace(',', ''))*1000)
            stockPreRev.append([dict2[i][0], [ttm,ttm_v,ttmg_v], [pre,pre_v,preg_v]])
        else :
            ttm = txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[1]/div/div[2]')
            #
            ttm_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[1]/div[1]/div[2]').replace(',', ''))*1000)
            #
            ttmg_v = '{:,}'.format(int(txt('//*[@id="Col1-1-Financials-Proxy"]/section/div[3]/div[1]/div/div[2]/div[3]/div[1]/div[2]').replace(',', ''))*1000)
            stockPreRev.append([dict2[i][0], [ttm,ttm_v,ttmg_v]])

    print(stockPreRev)
    
    
    
    def wp_post(text, ticker):
        url_base = '*****'
        url = urljoin(url_base, 'wp-json/wp/v2/posts/')
    
        user = 'user' # ユーザー名
        password = '*****'
        
        post = {
            'title': f'【米国株決算】${ticker}が決算発表間近！${ticker}の会計情報まとめ<br>',
            'status': 'publish', # draft(下書き), publish(公開)
            'slug': f'{dict2[i][0]}', # パーマリンク
            'categories': 2, # カテゴリID
            'date': datetime.now().isoformat(),
            'content': text,
            'featured_media' : 167       #アイキャッチ画像
        }
    
        res = requests.post(
            url,
            json=post,
            auth=(user, password),
            )
        return
    
    
    
    for i in range(0, len(dict2)):
        ticker = dict2[i][0]
        ######### tweet 取得
        def create_url(query, tweet_fields):
            if(any(tweet_fields)):
                formatted_tweet_fields = "tweet.fields=" + ",".join(tweet_fields)
            else:
                formatted_tweet_fields = ""
    
            url = "https://api.twitter.com/2/tweets/search/recent?query={}&{}&{}".format(
                query, formatted_tweet_fields, "expansions=author_id"
            )
            return url
    
        def create_headers(bearer_token):
            headers = {"Authorization": "Bearer {}".format(bearer_token)}
            return headers
    
        def connect_to_endpoint(url, headers):
            response = requests.request("GET", url, headers=headers)
            print(response.status_code)
            if response.status_code != 200:
                raise Exception(response.status_code, response.text)
            return response.json()
    
        def main():
            # bearer_token = auth()
            BEARER_TOKEN = r"*****"
            query = f"{ticker} (決算 OR 株)"
            # 検索ワード  e.g. query = "テスト" / query = "テスト OR test"
            # OR 検索　AND検索　-検索　などしたい場合はそのように書く
            tweet_fields = ["created_at", "author_id"] 
            # 取得データ  e.g. tweet_fields = ["created_at", "author_id"]
            # 空の場合は ツイートのid, text のみ取得する。
            # created_at(投稿時刻), author_id(アカウントID)などの情報が欲しい場合はtweet_fieldsに書く
    
            url = create_url(query, tweet_fields)
            headers = create_headers(BEARER_TOKEN)
            json_response = connect_to_endpoint(url, headers)
            result_text = json.dumps(json_response, indent=4, sort_keys=True, ensure_ascii=False)
            # 修正
            ids = []
            tweet_url_list = []
            search_timeline = json.loads(result_text)
            result_count = search_timeline['meta']['result_count']
            if result_count >= 3:
                for i in range(0, len(json.loads(json.dumps(json_response["data"])))):
                    ids.append([json.dumps(json_response["data"][i]["id"]).replace('"', '')])
                for i in range(0, len(json.loads(json.dumps(json_response["includes"]["users"])))):
                    ids[i].append(json.dumps(json_response["includes"]["users"][i]["username"]).replace('"', ''))
                for i in range(0, len(json.loads(json.dumps(json_response["includes"]["users"])))):
                    tweet_url = "https://twitter.com/{}/status/{}".format(ids[i][1], ids[i][0])
                    tweet_url_list.append(tweet_url)
                print(ids)
                return tweet_url_list
            elif result_count == 1:
                for i in range(0, len(json.loads(json.dumps(json_response["data"])))):
                    ids.append([json.dumps(json_response["data"][i]["id"]).replace('"', '')])
                for i in range(0, len(json.loads(json.dumps(json_response["includes"]["users"])))):
                    ids[i].append(json.dumps(json_response["includes"]["users"][i]["username"]).replace('"', ''))
                for i in range(0, len(json.loads(json.dumps(json_response["includes"]["users"])))):
                    tweet_url = "https://twitter.com/{}/status/{}".format(ids[i][1], ids[i][0])
                    tweet_url_list.append(tweet_url)
                print(ids)
                tweet_url_list.append("")
                tweet_url_list.append("")
                return tweet_url_list
            elif result_count == 2:
                for i in range(0, len(json.loads(json.dumps(json_response["data"])))):
                    ids.append([json.dumps(json_response["data"][i]["id"]).replace('"', '')])
                for i in range(0, len(json.loads(json.dumps(json_response["includes"]["users"])))):
                    ids[i].append(json.dumps(json_response["includes"]["users"][i]["username"]).replace('"', ''))
                for i in range(0, len(json.loads(json.dumps(json_response["includes"]["users"])))):
                    tweet_url = "https://twitter.com/{}/status/{}".format(ids[i][1], ids[i][0])
                    tweet_url_list.append(tweet_url)
                print(ids)
                tweet_url_list.append("")
                return tweet_url_list
            else:
                tweet_url_list = ["","",""]
                return tweet_url_list
    
        tweet_url_list = main()
    
    
    
        if len(stockPreRev) == 6:

            text = f'\
ここでは{tommorow}に決算を控えた${dict2[i][0]}について、会社情報と会計情報の面からお届けいたします。\n\
<h1>${dict2[i][0]}の基本情報</h1>\n\
<h2>事業内容</h2>\n\
<blockquote cite="https://finance.yahoo.co.jp/">{stockInformation[i][1]}\n\
\n\
<cite><a href="https://finance.yahoo.co.jp/">yahooファイナンス</a></cite></blockquote>\n\
<h2>会社概要</h2>\n\
<table>\n\
<tbody><!--\n\
<tr>\n\
<th></th>\n\
<th></th>\n\
</tr>\n\
-->\n\
<tr>\n\
<td>ティッカー</td>\n\
<td>${dict2[i][0]}</td>\n\
</tr>\n\
<tr>\n\
<td>設立</td>\n\
<td>{stockInformation[i][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>業種</td>\n\
<td>{stockInformation[i][3]}</td>\n\
</tr>\n\
<tr>\n\
<td>上場マーケット</td>\n\
<td>{stockInformation[i][4]}</td>\n\
</tr>\n\
<tr>\n\
<td>従業員数</td>\n\
<td>{stockInformation[i][5]}</td>\n\
</tr>\n\
<tr>\n\
<td>ホームページ</td>\n\
<td>{stockInformation[i][6]}</td>\n\
</tr>\n\
</tbody>\n\
</table>\n\
<h1>直近の業績</h1>\n\
<strong>YoY {stockYoy[i][3]}</strong>\n\
<table>\n\
<tbody>\n\
<tr>\n\
<th>売上の推移</th>\n\
<th>売上</th>\n\
<th>利益</th>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][1][0]}</td>\n\
<td>${stockPreRev[i][1][1]}</td>\n\
<td>${stockPreRev[i][1][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][2][0]}</td>\n\
<td>${stockPreRev[i][2][1]}</td>\n\
<td>${stockPreRev[i][2][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][3][0]}</td>\n\
<td>${stockPreRev[i][3][1]}</td>\n\
<td>${stockPreRev[i][3][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][4][0]}</td>\n\
<td>${stockPreRev[i][4][1]}</td>\n\
<td>${stockPreRev[i][4][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][5][0]}</td>\n\
<td>${stockPreRev[i][5][1]}</td>\n\
<td>${stockPreRev[i][5][2]}</td>\n\
</tr>\n\
</tbody>\n\
</table>\n\
<h1>コンセンサス</h1>\n\
予想EPS {stockYoy[i][1]}\n\
予想売上 ${stockYoy[i][2]}\n\
<h1>決算で注目すべき点</h1>\n\
予想EPS {stockYoy[i][1]}\n\
予想売上 ${stockYoy[i][2]}\n\
<h1>twitterの反応</h1>\n\
{tweet_url_list[0]}\n\
{tweet_url_list[1]}\n\
{tweet_url_list[2]}\n\
'
        elif len(stockPreRev) == 5:
            text = f'\
ここでは{tommorow}に決算を控えた${dict2[i][0]}について、会社情報と会計情報の面からお届けいたします。\n\
<h1>${dict2[i][0]}の基本情報</h1>\n\
<h2>事業内容</h2>\n\
<blockquote cite="https://finance.yahoo.co.jp/">{stockInformation[i][1]}\n\
\n\
<cite><a href="https://finance.yahoo.co.jp/">yahooファイナンス</a></cite></blockquote>\n\
<h2>会社概要</h2>\n\
<table>\n\
<tbody><!--\n\
<tr>\n\
<th></th>\n\
<th></th>\n\
</tr>\n\
-->\n\
<tr>\n\
<td>ティッカー</td>\n\
<td>${dict2[i][0]}</td>\n\
</tr>\n\
<tr>\n\
<td>設立</td>\n\
<td>{stockInformation[i][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>業種</td>\n\
<td>{stockInformation[i][3]}</td>\n\
</tr>\n\
<tr>\n\
<td>上場マーケット</td>\n\
<td>{stockInformation[i][4]}</td>\n\
</tr>\n\
<tr>\n\
<td>従業員数</td>\n\
<td>{stockInformation[i][5]}</td>\n\
</tr>\n\
<tr>\n\
<td>ホームページ</td>\n\
<td>{stockInformation[i][6]}</td>\n\
</tr>\n\
</tbody>\n\
</table>\n\
<h1>直近の業績</h1>\n\
<strong>YoY {stockYoy[i][3]}</strong>\n\
<table>\n\
<tbody>\n\
<tr>\n\
<th>売上の推移</th>\n\
<th>売上</th>\n\
<th>利益</th>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][1][0]}</td>\n\
<td>${stockPreRev[i][1][1]}</td>\n\
<td>${stockPreRev[i][1][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][2][0]}</td>\n\
<td>${stockPreRev[i][2][1]}</td>\n\
<td>${stockPreRev[i][2][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][3][0]}</td>\n\
<td>${stockPreRev[i][3][1]}</td>\n\
<td>${stockPreRev[i][3][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][4][0]}</td>\n\
<td>${stockPreRev[i][4][1]}</td>\n\
<td>${stockPreRev[i][4][2]}</td>\n\
</tr>\n\
</tbody>\n\
</table>\n\
<h1>コンセンサス</h1>\n\
予想EPS {stockYoy[i][1]}\n\
予想売上 ${stockYoy[i][2]}\n\
<h1>決算で注目すべき点</h1>\n\
予想EPS {stockYoy[i][1]}\n\
予想売上 ${stockYoy[i][2]}\n\
<h1>twitterの反応</h1>\n\
{tweet_url_list[0]}\n\
{tweet_url_list[1]}\n\
{tweet_url_list[2]}\n\
'
        elif len(stockPreRev) == 4:
            text = f'\
ここでは{tommorow}に決算を控えた${dict2[i][0]}について、会社情報と会計情報の面からお届けいたします。\n\
<h1>${dict2[i][0]}の基本情報</h1>\n\
<h2>事業内容</h2>\n\
<blockquote cite="https://finance.yahoo.co.jp/">{stockInformation[i][1]}\n\
\n\
<cite><a href="https://finance.yahoo.co.jp/">yahooファイナンス</a></cite></blockquote>\n\
<h2>会社概要</h2>\n\
<table>\n\
<tbody><!--\n\
<tr>\n\
<th></th>\n\
<th></th>\n\
</tr>\n\
-->\n\
<tr>\n\
<td>ティッカー</td>\n\
<td>${dict2[i][0]}</td>\n\
</tr>\n\
<tr>\n\
<td>設立</td>\n\
<td>{stockInformation[i][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>業種</td>\n\
<td>{stockInformation[i][3]}</td>\n\
</tr>\n\
<tr>\n\
<td>上場マーケット</td>\n\
<td>{stockInformation[i][4]}</td>\n\
</tr>\n\
<tr>\n\
<td>従業員数</td>\n\
<td>{stockInformation[i][5]}</td>\n\
</tr>\n\
<tr>\n\
<td>ホームページ</td>\n\
<td>{stockInformation[i][6]}</td>\n\
</tr>\n\
</tbody>\n\
</table>\n\
<h1>直近の業績</h1>\n\
<strong>YoY {stockYoy[i][3]}</strong>\n\
<table>\n\
<tbody>\n\
<tr>\n\
<th>売上の推移</th>\n\
<th>売上</th>\n\
<th>利益</th>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][1][0]}</td>\n\
<td>${stockPreRev[i][1][1]}</td>\n\
<td>${stockPreRev[i][1][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][2][0]}</td>\n\
<td>${stockPreRev[i][2][1]}</td>\n\
<td>${stockPreRev[i][2][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][3][0]}</td>\n\
<td>${stockPreRev[i][3][1]}</td>\n\
<td>${stockPreRev[i][3][2]}</td>\n\
</tr>\n\
</tbody>\n\
</table>\n\
<h1>コンセンサス</h1>\n\
予想EPS {stockYoy[i][1]}\n\
予想売上 ${stockYoy[i][2]}\n\
<h1>決算で注目すべき点</h1>\n\
予想EPS {stockYoy[i][1]}\n\
予想売上 ${stockYoy[i][2]}\n\
<h1>twitterの反応</h1>\n\
{tweet_url_list[0]}\n\
{tweet_url_list[1]}\n\
{tweet_url_list[2]}\n\
'
        elif len(stockPreRev) == 3:
            text = f'\
ここでは{tommorow}に決算を控えた${dict2[i][0]}について、会社情報と会計情報の面からお届けいたします。\n\
<h1>${dict2[i][0]}の基本情報</h1>\n\
<h2>事業内容</h2>\n\
<blockquote cite="https://finance.yahoo.co.jp/">{stockInformation[i][1]}\n\
\n\
<cite><a href="https://finance.yahoo.co.jp/">yahooファイナンス</a></cite></blockquote>\n\
<h2>会社概要</h2>\n\
<table>\n\
<tbody><!--\n\
<tr>\n\
<th></th>\n\
<th></th>\n\
</tr>\n\
-->\n\
<tr>\n\
<td>ティッカー</td>\n\
<td>${dict2[i][0]}</td>\n\
</tr>\n\
<tr>\n\
<td>設立</td>\n\
<td>{stockInformation[i][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>業種</td>\n\
<td>{stockInformation[i][3]}</td>\n\
</tr>\n\
<tr>\n\
<td>上場マーケット</td>\n\
<td>{stockInformation[i][4]}</td>\n\
</tr>\n\
<tr>\n\
<td>従業員数</td>\n\
<td>{stockInformation[i][5]}</td>\n\
</tr>\n\
<tr>\n\
<td>ホームページ</td>\n\
<td>{stockInformation[i][6]}</td>\n\
</tr>\n\
</tbody>\n\
</table>\n\
<h1>直近の業績</h1>\n\
<strong>YoY {stockYoy[i][3]}</strong>\n\
<table>\n\
<tbody>\n\
<tr>\n\
<th>売上の推移</th>\n\
<th>売上</th>\n\
<th>利益</th>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][1][0]}</td>\n\
<td>${stockPreRev[i][1][1]}</td>\n\
<td>${stockPreRev[i][1][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][2][0]}</td>\n\
<td>${stockPreRev[i][2][1]}</td>\n\
<td>${stockPreRev[i][2][2]}</td>\n\
</tr>\n\
</tbody>\n\
</table>\n\
<h1>コンセンサス</h1>\n\
予想EPS {stockYoy[i][1]}\n\
予想売上 ${stockYoy[i][2]}\n\
<h1>決算で注目すべき点</h1>\n\
予想EPS {stockYoy[i][1]}\n\
予想売上 ${stockYoy[i][2]}\n\
<h1>twitterの反応</h1>\n\
{tweet_url_list[0]}\n\
{tweet_url_list[1]}\n\
{tweet_url_list[2]}\n\
'
        elif len(stockPreRev) == 2:
            text = f'\
ここでは{tommorow}に決算を控えた${dict2[i][0]}について、会社情報と会計情報の面からお届けいたします。\n\
<h1>${dict2[i][0]}の基本情報</h1>\n\
<h2>事業内容</h2>\n\
<blockquote cite="https://finance.yahoo.co.jp/">{stockInformation[i][1]}\n\
\n\
<cite><a href="https://finance.yahoo.co.jp/">yahooファイナンス</a></cite></blockquote>\n\
<h2>会社概要</h2>\n\
<table>\n\
<tbody><!--\n\
<tr>\n\
<th></th>\n\
<th></th>\n\
</tr>\n\
-->\n\
<tr>\n\
<td>ティッカー</td>\n\
<td>${dict2[i][0]}</td>\n\
</tr>\n\
<tr>\n\
<td>設立</td>\n\
<td>{stockInformation[i][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>業種</td>\n\
<td>{stockInformation[i][3]}</td>\n\
</tr>\n\
<tr>\n\
<td>上場マーケット</td>\n\
<td>{stockInformation[i][4]}</td>\n\
</tr>\n\
<tr>\n\
<td>従業員数</td>\n\
<td>{stockInformation[i][5]}</td>\n\
</tr>\n\
<tr>\n\
<td>ホームページ</td>\n\
<td>{stockInformation[i][6]}</td>\n\
</tr>\n\
</tbody>\n\
</table>\n\
<h1>直近の業績</h1>\n\
<strong>YoY {stockYoy[i][3]}</strong>\n\
<table>\n\
<tbody>\n\
<tr>\n\
<th>売上の推移</th>\n\
<th>売上</th>\n\
<th>利益</th>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][1][0]}</td>\n\
<td>${stockPreRev[i][1][1]}</td>\n\
<td>${stockPreRev[i][1][2]}</td>\n\
</tr>\n\
<tr>\n\
<td>{stockPreRev[i][2][0]}</td>\n\
<td>${stockPreRev[i][2][1]}</td>\n\
<td>${stockPreRev[i][2][2]}</td>\n\
</tr>\n\
</tbody>\n\
</table>\n\
<h1>コンセンサス</h1>\n\
予想EPS {stockYoy[i][1]}\n\
予想売上 ${stockYoy[i][2]}\n\
<h1>決算で注目すべき点</h1>\n\
予想EPS {stockYoy[i][1]}\n\
予想売上 ${stockYoy[i][2]}\n\
<h1>twitterの反応</h1>\n\
{tweet_url_list[0]}\n\
{tweet_url_list[1]}\n\
{tweet_url_list[2]}\n\
'
    
        """ f = open('teststock{}.txt'.format(i), 'w')
        f.write(text)
        f.close """
        wp_post(text,dict2[i][0])
    
    
    
    
    
    
    
    
    time.sleep(2)
    #driver.close()
    
    
    
    
    
    
    
    
    
    
    
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
