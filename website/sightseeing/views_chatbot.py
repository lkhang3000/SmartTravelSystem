# Django API cho chatbot Gemini - CHỈ BACKEND
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
import json
import os

# Import Gemini
try:
    import google.generativeai as genai
except ImportError:
    genai = None


@ensure_csrf_cookie
@require_http_methods(["POST"])
def chat_with_gemini(request):
    """
    API endpoint đơn giản để chat với Gemini 2.0 Flash
    
    POST /api/chat/
    Request Body: {"message": "câu hỏi của user"}
    
    Response Success:
    {
        "success": true,
        "reply": "câu trả lời từ Gemini"
    }
    
    Response Error:
    {
        "error": "mô tả lỗi"
    }
    """
    
    if not genai:
        return JsonResponse({
            'error': 'Chưa cài đặt google-generativeai. Chạy: pip install google-generativeai'
        }, status=500)
    
    try:
        # Lấy message từ request
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        if not user_message:
            return JsonResponse({'error': 'Không có message'}, status=400)
        
        # Lấy API key từ environment
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return JsonResponse({
                'error': 'Chưa set GEMINI_API_KEY. Xem QUICKSTART_CHATBOT.md'
            }, status=500)
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Khởi tạo model Gemini 2.0 Flash
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Gửi message và nhận response
        response = model.generate_content(user_message)
        
        # Trả về JSON
        return JsonResponse({
            'success': True,
            'reply': response.text
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Lỗi: {str(e)}'
        }, status=500)

