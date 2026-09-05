# My GPT — Python + HTML/CSS/JS

نسخه ساده و آموزشی پروژه AI Study Planner.

## اجرا

1. Python را نصب کنید.
2. در ترمینال، داخل همین پوشه اجرا کنید:

```bash
pip install -r requirements.txt
python app.py
```

بعد مرورگر به‌صورت خودکار روی این آدرس باز می‌شود:

`http://127.0.0.1:8000`

## API Key

در ابتدای `app.py` مقدار زیر را تغییر دهید:

```python
API_KEY = "YOUR_OPENROUTER_API_KEY"
```

یا متغیر محیطی `OPENROUTER_API_KEY` را تنظیم کنید.

## معماری آموزشی

Browser (HTML/CSS/JS)
→ `fetch("/api/plan")`
→ Python `http.server`
→ `generate_plan()`
→ OpenRouter
→ JSON
→ Browser

هیچ فریم‌ورکی مثل Flask یا FastAPI استفاده نشده است.
