import json
import os
# import random
from datetime import datetime, timedelta, timezone
from string import ascii_uppercase

import requests
from bs4 import BeautifulSoup
import pandas as pd

from dotenv import load_dotenv
load_dotenv()

# 設定登入憑證
USER_ID = os.getenv("USER_ID", "USER_ID")
PASSWORD = os.getenv("PASSWORD", "PASSWORD")

# 生成隨機驗證碼
# RANDOM_CODE = "".join(random.choices(ascii_uppercase, k=4))

# https://onepiece2-sso.nchu.edu.tw/cofsys/plsql/acad_subpasschk1?v_subname=vocscrd_table

with requests.Session() as session:
    # 設定 cookie 過期時間
    expires = (datetime.now(timezone.utc) + timedelta(days=30)).timestamp()

    # 設定請求標頭
    session.headers.setdefault(
        "User-Agent",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
    )
    session.cookies.set(
        "login", json.dumps([{"time": str(int(expires))}, {"time": str(int(expires + 30 * 1000))}])
    )
    
    # 執行登入流程
    session.get("https://idp.nchu.edu.tw/nidp/idff/sso?id=12&sid=0&option=credential&sid=0&target=")
    login_req = session.post(
        "https://idp.nchu.edu.tw/nidp/idff/sso?sid=5",
        data={
            "Ecom_User_ID": USER_ID,
            "Ecom_Password": PASSWORD,
            # "inputCode": RANDOM_CODE,
            "option": "credential",
            "target": "https://onepiece2-sso.nchu.edu.tw/cofsys/plsql/acad_subpasschk1?v_subname=vocscrd_table",
        },
        headers={"Content-type": "application/x-www-form-urlencoded"},
    )

    # 獲取課表頁面
    redirect_url = "https://onepiece2-sso.nchu.edu.tw/cofsys/plsql/acad_subpasschk1?v_subname=vocscrd_table"
    response = session.get(redirect_url, allow_redirects=True)
    data_url = "https://onepiece2-sso.nchu.edu.tw/cofsys/plsql/vocscrd_table"
    data_response = session.get(data_url)
    
    # 解析HTML
    soup = BeautifulSoup(data_response.text, 'html.parser')
    
    # 找到主要的課表表格（通常是第二個表格，第一個是標題）
    tables = soup.find_all('table')
    if len(tables) >= 2:
        main_table = tables[1]  # 獲取課表主體
        
        # 設定表頭
        headers = ['時間']
        for th in main_table.find_all('td')[1:8]:
            headers.append(th.text.strip())
        
        # 提取課程資料
        rows = []
        for tr in main_table.find_all('tr')[1:]:
            row_data = []
            for td in tr.find_all('td'):
                # 只提取課程名稱
                if '(' in td.text:
                    course_name = td.text.split('(')[0].strip()
                    row_data.append(course_name)
                else:
                    row_data.append(td.text.strip().replace('\u3000', ''))
            rows.append(row_data)
        
        # 建立DataFrame
        df = pd.DataFrame(rows, columns=headers)
        
        # 提取標題表格資訊
        title_table = tables[0].find_all('td')
        
        # 解析並顯示標題資訊
        student_info = title_table[0].text.strip()  # 學生資訊
        date_info = title_table[1].text.strip()     # 日期資訊
        
        print(student_info)
        print(date_info)
        
        # 顯示課表內容
        print("\n每週課表：")
        print(df)
