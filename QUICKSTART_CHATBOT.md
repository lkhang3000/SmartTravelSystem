# 🚀 QUICK START - Chatbot Gemini (2 phút)

## Bước 1: Cài đặt
```bash
pip install google-generativeai
```

## Bước 2: Lấy API Key
1. Truy cập: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy key

## Bước 3: Set API Key

**Windows (CMD - vĩnh viễn):**
```cmd
setx GEMINI_API_KEY "AIzaSy_YOUR_KEY_HERE"
```
Sau đó **RESTART TERMINAL**

**Hoặc tạo file `.env`:**
```
GEMINI_API_KEY=AIzaSy_YOUR_KEY_HERE
```

## Bước 4: Test
```bash
python manage.py runserver
```

Truy cập: http://localhost:8000/

Click vào biểu tượng chatbot 💬 ở góc dưới bên phải.

---

## ✅ Chatbot đã được tích hợp

Chatbot đã được tích hợp vào `homepage.html` với:
- Icon chatbot góc dưới bên phải (💬)
- Kết nối với Gemini 2.0 Flash API
- Backend endpoint: `/api/chat/`
- Giao diện đã có sẵn, chỉ cần set API key

**KHÔNG cần thêm file JS nào khác vào template!**

---

## 📚 Chi tiết

Xem file `SETUP_GEMINI_CHATBOT.md` để:
- Customize giao diện
- Thêm prompt
- Tích hợp database
- Advanced features

---

## 🎯 Cho BE Team

File cần chú ý:
- `sightseeing/views_chatbot.py` - Backend logic (EDIT HERE)
- `sightseeing/Templates/homepage.html` - Frontend widget (JavaScript ở cuối file)
- API endpoint: `/api/chat/`

Thêm prompt (system instruction):
```python
model = genai.GenerativeModel(
    'gemini-2.0-flash-exp',
    system_instruction="Bạn là trợ lý du lịch Việt Nam chuyên nghiệp..."  # ← EDIT HERE
)
```

Thay đổi giao diện chatbot:
- Edit CSS trong `<style>` section của `homepage.html`
- Tìm class `.chat-container`, `.chat-button`, `.chat-box`, etc.
