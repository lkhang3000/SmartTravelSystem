# 🤖 HƯỚNG DẪN SETUP CHATBOT GEMINI 2.0 FLASH

## 📋 Tổng Quan

Chatbot đơn giản tích hợp Google Gemini 2.0 Flash vào website Django.
- ✅ Không cần prompt phức tạp
- ✅ Giao diện chat đẹp, responsive
- ✅ Dễ dàng customize cho BE team

---

## 🚀 BƯỚC 1: Cài Đặt Thư Viện

```bash
pip install google-generativeai
```

---

## 🔑 BƯỚC 2: Lấy Gemini API Key

### 1. Truy cập Google AI Studio:
```
https://aistudio.google.com/app/apikey
```

### 2. Đăng nhập bằng Google Account

### 3. Click "Create API Key"

### 4. Copy API key (dạng: AIzaSy...)

### 5. Thêm vào Environment Variable:

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="AIzaSy_YOUR_KEY_HERE"
```

**Windows (CMD - vĩnh viễn):**
```cmd
setx GEMINI_API_KEY "AIzaSy_YOUR_KEY_HERE"
```
Sau đó restart terminal

**Linux/Mac:**
```bash
export GEMINI_API_KEY="AIzaSy_YOUR_KEY_HERE"
```

Hoặc thêm vào `.env` file (khuyên dùng):
```
GEMINI_API_KEY=AIzaSy_YOUR_KEY_HERE
```

---

## ⚙️ BƯỚC 3: Cấu Hình Django

### 1. Thêm URLs vào `website/urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... các URLs khác
    path('', include('sightseeing.urls_chatbot')),
]
```

### 2. Nếu dùng `.env` file, cài python-decouple:

```bash
pip install python-decouple
```

Trong `settings.py`:
```python
from decouple import config

# ... existing code ...

# Gemini API Key
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
```

Sửa `views_chatbot.py` dòng 29:
```python
# Thay vì:
api_key = os.environ.get('GEMINI_API_KEY')

# Dùng:
from django.conf import settings
api_key = settings.GEMINI_API_KEY
```

---

## 🎨 BƯỚC 4: Thêm Chatbot Vào Website

### Cách 1: Thêm vào base template (áp dụng cho tất cả trang)

Mở file base template (vd: `base.html` hoặc `Home.html`):

```html
<!DOCTYPE html>
<html>
<head>
    <!-- ... head content ... -->
</head>
<body>
    <!-- Nội dung website -->
    
    <!-- Thêm trước tag </body> -->
    {% load static %}
    <script src="{% static 'js/gemini-chatbot.js' %}"></script>
</body>
</html>
```

### Cách 2: Thêm vào trang cụ thể

Trong template bất kỳ, thêm:
```html
{% load static %}
<script src="{% static 'js/gemini-chatbot.js' %}"></script>
```

---

## ✅ BƯỚC 5: Test Chatbot

### 1. Chạy Django server:
```bash
python manage.py runserver
```

### 2. Truy cập trang test:
```
http://localhost:8000/chatbot/test/
```

### 3. Click vào icon chatbot góc dưới bên phải

### 4. Chat thử!

---

## 📁 Cấu Trúc Files

```
website/
├── sightseeing/
│   ├── views_chatbot.py          # ⭐ Backend API
│   ├── urls_chatbot.py            # URLs cho chatbot
│   ├── Static/
│   │   └── js/
│   │       └── gemini-chatbot.js  # ⭐ Frontend widget
│   └── Templates/
│       └── chatbot_test.html      # Trang test
```

---

## 🎯 API Endpoint

### POST `/api/chat/`

**Request:**
```json
{
  "message": "Gợi ý địa điểm du lịch Đà Nẵng"
}
```

**Response (Success):**
```json
{
  "success": true,
  "reply": "Đà Nẵng có nhiều địa điểm đẹp như..."
}
```

**Response (Error):**
```json
{
  "error": "Lỗi: ..."
}
```

---

## 🔧 Customize Cho BE Team

### 1. Thay đổi model Gemini:

Trong `views_chatbot.py`:
```python
# Thay đổi model
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Các model khác:
# - 'gemini-1.5-pro' (thông minh hơn)
# - 'gemini-1.5-flash' (nhanh hơn)
```

### 2. Thêm system prompt:

```python
model = genai.GenerativeModel(
    'gemini-2.0-flash-exp',
    system_instruction="Bạn là trợ lý du lịch Việt Nam chuyên nghiệp..."
)
```

### 3. Thêm chat history:

```python
# Lưu history trong session
chat = model.start_chat(history=[
    {"role": "user", "parts": ["Xin chào"]},
    {"role": "model", "parts": ["Chào bạn!"]},
])

response = chat.send_message(user_message)
```

### 4. Thêm streaming response:

```python
response = model.generate_content(user_message, stream=True)
for chunk in response:
    # Gửi chunk qua WebSocket hoặc SSE
    pass
```

### 5. Thêm safety settings:

```python
from google.generativeai.types import HarmCategory, HarmBlockThreshold

model = genai.GenerativeModel(
    'gemini-2.0-flash-exp',
    safety_settings={
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    }
)
```

---

## 🎨 Customize Giao Diện

### Thay đổi màu sắc:

Trong `gemini-chatbot.js`, tìm và sửa:

```css
/* Gradient màu chính */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Thay bằng màu của bạn: */
background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%);
```

### Thay đổi vị trí:

```css
#gemini-chatbot {
    bottom: 20px;   /* Khoảng cách từ dưới */
    right: 20px;    /* Khoảng cách từ phải */
    
    /* Để bên trái: */
    /* left: 20px; */
    /* right: auto; */
}
```

### Thay đổi kích thước:

```css
#chatbot-window {
    width: 350px;   /* Độ rộng */
    height: 500px;  /* Độ cao */
}
```

---

## ❓ Troubleshooting

### Lỗi: "Gemini chưa được cài đặt"
```bash
pip install google-generativeai
```

### Lỗi: "Chưa có GEMINI_API_KEY"
- Kiểm tra đã set environment variable chưa
- Restart terminal sau khi setx
- Hoặc dùng `.env` file

### Lỗi: "Import google.generativeai could not be resolved"
- Đã cài thư viện nhưng vẫn lỗi → restart VS Code
- Kiểm tra Python interpreter đúng

### Chatbot không hiện
- Kiểm tra console browser (F12) có lỗi JS không
- Đảm bảo đã load `gemini-chatbot.js`
- Kiểm tra CSS conflict với website

### API không hoạt động
- Kiểm tra URL endpoint: `/api/chat/`
- Xem Django console có lỗi không
- Test bằng Postman/curl trước

---

## 💡 Next Steps Cho BE Team

1. **Thêm prompt cho du lịch**:
   - Context về địa điểm trong database
   - Personality cho chatbot (thân thiện, chuyên nghiệp...)
   - Format câu trả lời

2. **Tích hợp với database**:
   - Query địa điểm từ `Destinations` model
   - Đưa context vào prompt Gemini
   - Trả về link/ảnh địa điểm

3. **Chat history**:
   - Lưu conversation trong session/database
   - Maintain context giữa các tin nhắn

4. **Rate limiting**:
   - Giới hạn số request/user
   - Cache responses phổ biến

5. **Analytics**:
   - Track số lượng conversations
   - Phân tích câu hỏi thường gặp

---

## 📞 Support

- Google AI Studio: https://aistudio.google.com
- Gemini API Docs: https://ai.google.dev/docs
- Python SDK: https://github.com/google/generative-ai-python

---

**✅ Setup xong! Chatbot đã sẵn sàng. BE team có thể bắt đầu customize!**
