import requests
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv
load_dotenv()

# 設定登入憑證
USER_ID = os.getenv("USER_ID", "USER_ID")
PASSWORD = os.getenv("PASSWORD", "PASSWORD")

class NCHULMSLogin:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://lms2020.nchu.edu.tw"
        self.login_url = f"{self.base_url}/index/login"
        self.captcha_url = f"{self.base_url}/sys/libs/class/capcha/secimg.php?charLens=6&codeType=num"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_captcha(self):
        """獲取驗證碼圖片並返回圖片內容"""
        response = self.session.get(self.captcha_url, headers=self.headers)
        if response.status_code == 200:
            return response.content
        return None

    def login(self, account, password):
        """執行登入並返回結果字典"""
        # 獲取登入頁面和 CSRF token
        response = self.session.get(self.login_url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrf-t'})
        csrf_token = csrf_input['value'] if csrf_input else None

        if not csrf_token:
            return {"success": False, "message": "無法獲取 CSRF token"}

        # 獲取驗證碼
        captcha_image = self.get_captcha()
        if not captcha_image:
            return {"success": False, "message": "無法獲取驗證碼"}

        # 保存驗證碼圖片供OCR使用
        with open('captcha.png', 'wb') as f:
            f.write(captcha_image)

        # 使用OCR識別驗證碼
        try:
            from OCR_Captcha import process_captcha
            captcha = process_captcha()
        except Exception as e:
            return {"success": False, "message": f"驗證碼識別失敗: {str(e)}"}

        # 提交登入表單
        login_data = {
            'account': account,
            'password': password,
            'csrf-t': csrf_token,
            '_fmSubmit': 'yes',
            'formVer': '3.0',
            'formId': 'login_form',
            'next': '/dashboard',
            'captcha': captcha
        }

        response = self.session.post(
            self.login_url, 
            data=login_data,
            headers=self.headers
        )

        try:
            response_json = response.json()
            if response_json.get('ret', {}).get('status') == 'true':
                phpsessid = self.session.cookies.get('PHPSESSID')
                # dashboard_content = self.get_dashboard_content()
                return {
                    "success": True,
                    "message": "登入成功",
                    "phpsessid": phpsessid,
                    # "dashboard_content": dashboard_content
                }
            else:
                error_msg = response_json.get('msg') or response_json.get('ret', {}).get('msg')
                return {
                    "success": False,
                    "message": error_msg or "登入失敗"
                }
                
        except ValueError as e:
            return {
                "success": False,
                "message": f"解析回應失敗: {str(e)}"
            }

    def get_dashboard_lastEvent(self):
        """爬取最新事件內容並返回 JSON 格式"""
        response = self.session.get(
            f"{self.base_url}/dashboard/latestEvent",
            headers=self.headers
        )

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', id='recentEventTable')
            
            if table:
                events = []
                rows = table.find('tbody').find_all('tr')
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) == 3:  # 確保有三列（標題、來源、期限）
                        title_link = cols[0].find('a')
                        source_link = cols[1].find('a')
                        deadline = cols[2].find('div', class_='text-overflow')
                        
                        event = {
                            'title': title_link.find('span', class_='text').text.strip() if title_link else '',
                            'title_link': self.base_url + title_link['href'] if title_link else '',
                            'source': source_link.find('span', class_='text').text.strip() if source_link else '',
                            'source_link': self.base_url + source_link['href'] if source_link else '',
                            'deadline': deadline['title'] if deadline and 'title' in deadline.attrs else deadline.text.strip() if deadline else ''
                        }
                        events.append(event)
                
                return json.dumps({
                    "success": True,
                    "data": events
                }, ensure_ascii=False)
            
            return json.dumps({
                "success": False,
                "message": "找不到事件表格"
            }, ensure_ascii=False)
        
        return json.dumps({
            "success": False,
            "message": f"請求失敗: {response.status_code}"
        }, ensure_ascii=False)

if __name__ == "__main__":
    print("ilearning_login.py is running")