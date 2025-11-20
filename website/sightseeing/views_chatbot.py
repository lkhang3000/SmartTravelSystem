# file views_chatbot.py: # Django API for Gemini chatbot - BACKEND ONLY
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
import os

# Import Gemini
try:
    import google.generativeai as genai
except ImportError:
    genai = None
    APIError = type('APIError', (Exception,), {})  # Dummy error class for graceful handling


# --- SYSTEM INSTRUCTION (Fixed Prompt for the Chatbot) ---
SYSTEM_INSTRUCTION = """
You are 'VietTour Guide', a Vietnam travel expert for four destinations: Hue, Ho Chi Minh City (Saigon), Hanoi, and Ha Long Bay.

Your goal is to give short, focused, and practical travel answers.

### Response Rules:
1. **Scope:** Only answer questions about Hue, Ho Chi Minh City, Hanoi, Ha Long Bay, or combinations of these.
2. **Style:** Clear, friendly English. Keep answers brief and straight to the point.
3. **Format:** Use bullet points. Maximum 3–5 key points per answer.
4. **Out-of-scope:** If asked about another place, reply:
   "Sorry! I only specialize in Hue, Ho Chi Minh City, Hanoi, and Ha Long Bay. Would you like recommendations for these destinations?"
"""
# --------------------------------------------------------


@ensure_csrf_cookie
@require_http_methods(["POST"])
def chat_with_gemini(request):
    """
    Simple API endpoint to chat with Gemini 2.0 Flash
    
    POST /api/chat/
    Request Body: {"message": "user question"}
    """
    
    if not genai:
        return JsonResponse({
            'error': 'google-generativeai is not installed. Run: pip install google-generativeai'
        }, status=500)
    
    try:
        # Get message from request
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        if not user_message:
            return JsonResponse({'error': 'No message provided'}, status=400)
        
        # Get API key from environment
        try:
            api_key = settings.GEMINI_API_KEY
        except AttributeError:
             return JsonResponse({
                'error': 'GEMINI_API_KEY not set in settings.py (or .env).'
            }, status=500)

        if not api_key:
            return JsonResponse({
                'error': 'GEMINI_API_KEY is empty. Please check your configuration.'
            }, status=500)
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Create full prompt: System Instruction + User Message
        full_prompt = f"{SYSTEM_INSTRUCTION}\n\nCustomer Question: \"{user_message}\""
        
        # Initialize Gemini 2.0 Flash model
        model = genai.GenerativeModel('gemini-2.0-flash')

        
        # Send message and get response
        response = model.generate_content(full_prompt)
        
        # Return JSON
        return JsonResponse({
            'success': True,
            'reply': response.text
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except APIError as e:
        # Handle errors from Google API (e.g., invalid API key, rate limit)
        return JsonResponse({
            'error': f'Gemini API error: {str(e)}'
        }, status=500)
    except Exception as e:
        # Handle general errors
        return JsonResponse({
            'error': f'Server error: {str(e)}'
        }, status=500)
