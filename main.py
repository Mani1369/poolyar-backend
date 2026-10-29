import json
import sys
import io
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

# رفع مشکل نمایش حروف فارسی در ویندوز (UTF-8)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ⚠️ کلید Groq خود را دقیقاً اینجا بین دو کوتیشن بگذارید
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=("GROQ_API_KEY") 
)

app = FastAPI(title="Poolyar API")

# تنظیمات برای اتصال فرانت‌اند (React) در آینده
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ساختار داده ورودی
class SMSRequest(BaseModel):
    text: str

# دیتابیس موقت در حافظه
transactions_db = []

@app.post("/api/analyze-sms")
async def analyze_sms(request: SMSRequest):
    sms_text = request.text
    
    # دستور (Prompt) به هوش مصنوعی
    prompt = f"""
    شما یک دستیار مالی هوشمند هستید. متن پیامک بانکی زیر را تحلیل کنید.
    متن پیامک: "{sms_text}"
    
    لطفاً اطلاعات زیر را استخراج کرده و فقط و فقط به صورت یک آبجکت JSON با کلیدهای انگلیسی برگردانید:
    - "amount": مبلغ تراکنش (فقط عدد، بدون کاما)
    - "category": دسته‌بندی تراکنش (فقط یکی از این کلمات: "Food", "Transport", "Bills", "Shopping", "Entertainment", "Income", "Other")
    - "merchant": نام فروشگاه یا شخص (اگر موجود بود)
    - "description": یک توضیح کوتاه فارسی از تراکنش
    
    خروجی شما باید دقیقاً یک JSON معتبر باشد و هیچ متن اضافه‌ای نداشته باشد.
    """
    
    try:
        # ارسال درخواست به Groq
        response = client.chat.completions.create(
           model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are a helpful financial assistant that outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        
        # دریافت پاسخ و تبدیل به دیکشنری
        ai_result = json.loads(response.choices[0].message.content)
        ai_result["original_text"] = sms_text
        
        # ذخیره در دیتابیس موقت
        transactions_db.append(ai_result)
        
        return ai_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API برای گرفتن لیست تراکنش‌ها (برای داشبورد)
@app.get("/api/transactions")
async def get_transactions():
    return {"transactions": transactions_db}

# API برای پاک کردن دیتابیس (برای تست مجدد)
@app.delete("/api/transactions")
async def clear_transactions():
    transactions_db.clear()
    return {"message": "Database cleared"}