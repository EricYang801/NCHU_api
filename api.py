from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from ilearning_Login import NCHULMSLogin
import uvicorn
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NCHU LMS API")

class LoginRequest(BaseModel):
    account: str
    password: str

@app.post("/login")
async def login(request: LoginRequest):
    """
    登入NCHU LMS系統
    
    參數:
    - account: 學號
    - password: 密碼
    
    返回:
    - success: 是否成功
    - message: 訊息
    - phpsessid: 如果成功，返回session ID
    """
    try:
        logger.info(f"收到登入請求: {request.account}")
        lms = NCHULMSLogin()
        result = lms.login(request.account, request.password)
        
        if not result["success"]:
            logger.error(f"登入失敗: {result['message']}")
            raise HTTPException(status_code=401, detail=result["message"])
        
        logger.info("登入成功")
        return result
    except Exception as e:
        logger.error(f"處理登入請求時發生錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """API根路徑"""
    return {"message": "NCHU LMS API server is running"}

if __name__ == "__main__":
    try:
        logger.info("正在啟動 API 服務器...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(f"啟動服務器時發生錯誤: {str(e)}") 