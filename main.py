import time
import requests
import json
import os

# 🔑 معلومات البوت
PAGE_ACCESS_TOKEN = 'EAAKL1CbcvhUBPUZCZBbvoOkg0i7P1JVe0RT2ZAhZBAcS25B2OuHC64xboQCZAoqKzexPq9DkVAeR5VqquGaUMo8cWvflccMm1ZC9hI5R5r2sHX75p33HywugHZAQbMXpJVHMlMVso2Y21YV3sM6jIKF8CI8sZCoZC37CHRTS7nh5EGtFZCOwOZBywbHEFdf6ZASVhDaDfvZAvZCwZDZD'
PAGE_ID = '775394682331190'
GROQ_API_KEY = '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'  

MODEL = "llama-3.1-8b-instant"  

# 📂 ملف الذاكرة
MEMORY_FILE = "memory.json"

# 🧠 تحميل الذاكرة عند بداية التشغيل
if os.path.exists(MEMORY_FILE):
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            user_memory = json.load(f)
    except:
        user_memory = {}
else:
    user_memory = {}

# 🔁 تخزين آخر رسالة
last_message_id = None

# 🧠 دالة حفظ الذاكرة
def save_memory():
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(user_memory, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("⚠️ خطأ في حفظ الذاكرة:", e)

# 🧠 دالة الرد بالذكاء الاصطناعي (مع retry لو تجاوز الحد)
def get_ai_reply(user_id, user_message):
    if user_id not in user_memory:
        user_memory[user_id] = []

    user_memory[user_id].append({"role": "user", "content": user_message})

    # نخلي المحادثة قصيرة (آخر 5 رسائل فقط لتقليل التوكنات)
    messages = [
        {
            "role": "system",
            "content": "انت مساعد افتراضي ذكي. تتحدث العربية فقط بدقة ووضوح. اجعل ردودك قصيرة ومفيدة."
        }
    ] + user_memory[user_id][-5:]

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 300
    }

    for attempt in range(3):  # جرّب 3 مرات
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            result = response.json()
            print("📡 رد Groq:", result)

            if "choices" in result:
                reply = result["choices"][0]["message"]["content"].strip()
                user_memory[user_id].append({"role": "assistant", "content": reply})
                save_memory()
                return reply

            elif "error" in result:
                error_msg = result["error"].get("message", "غير معروف")
                if "Rate limit" in error_msg and attempt < 2:
                    wait_time = 15  # انتظر 15 ثانية
                    print(f"⚠️ تم الوصول للحد، إعادة المحاولة بعد {wait_time} ثانية...")
                    time.sleep(wait_time)
                    continue
                return f"❌ خطأ من Groq API: {error_msg}"

            else:
                return "❌ لم يتم تلقي رد صحيح من الذكاء الاصطناعي."
        except Exception as e:
            print("❌ استثناء:", e)
            return "❌ حدث خطأ داخلي."

    return "❌ تعذر الحصول على رد بعد عدة محاولات."

# ✉️ إرسال رسالة
def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    try:
        requests.post(url, headers=headers, json=data)
    except Exception as e:
        print("❌ خطأ في إرسال الرسالة:", e)

# 📥 جلب آخر رسالة
def get_latest_message():
    url = f"https://graph.facebook.com/v18.0/{PAGE_ID}/conversations?fields=messages.limit(1){{message,id,from}}&access_token={PAGE_ACCESS_TOKEN}"
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print("❌ خطأ في جلب الرسائل:", e)
        return {}

# 🚀 تشغيل البوت
def run_bot():
    global last_message_id
    print("✅ بوت فيسبوك يعمل الآن (ذاكرة محفوظة + دقة أعلى + حماية من Rate Limit)...")
    while True:
        data = get_latest_message()
        try:
            if "data" in data and len(data["data"]) > 0:
                message = data["data"][0]["messages"]["data"][0]
                message_id = message["id"]
                sender_id = message["from"]["id"]
                text = message.get("message", "")

                if message_id != last_message_id and sender_id != PAGE_ID:
                    print(f"📨 رسالة جديدة من {sender_id}: {text}")

                    reply = get_ai_reply(sender_id, text)
                    send_message(sender_id, reply)

                    last_message_id = message_id
        except Exception as e:
            print("⚠️ خطأ في التشغيل:", e)

        time.sleep(4)

# ▶️ بدء التشغيل
run_bot()