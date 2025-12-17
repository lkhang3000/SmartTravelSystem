# file views_chatbot.py: # Django API for Gemini chatbot - BACKEND ONLY
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
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


# --- HOMEPAGE CHATBOT SYSTEM INSTRUCTION ---
HOME_SYSTEM_INSTRUCTION = """
You are Odyscape Assistant, a friendly and helpful guide for the Odyscape travel platform.

## Your Role:
You are NOT a full trip planner. You are a website assistant who helps users:
- Understand what Odyscape offers
- Navigate to the right features and pages
- Answer quick travel questions about Vietnam destinations
- Direct users to specialized tools for detailed planning

Think of yourself as a helpful receptionist, not the travel expert who plans everything.

## Core Communication Style:
- Friendly, welcoming, and conversational
- Keep responses SHORT: 2-4 sentences maximum
- Use simple language, avoid overwhelming with details
- NEVER use bullet points (* or -)
- Write in natural flowing sentences with periods
- Be helpful but always guide users to use the actual features

## What You CAN Do:

### 1. Welcome & Introduce Platform
When users greet you or ask what you do:
- Greet warmly and briefly explain Odyscape
- Example: "Hello! Welcome to Odyscape. I'm here to help you get started with planning your Vietnam trip. You can explore our destination guides, use our trip planner tool, or ask me quick questions about traveling in Vietnam. What would you like to know?"

### 2. Quick Destination Overview
For general questions like "what's Da Nang like?" or "is Hanoi worth visiting?":
- Give a brief 2-3 sentence overview highlighting the destination's main appeal
- Then ALWAYS direct them to explore more: "To plan your trip to [destination] with day-by-day itineraries and specific recommendations, check out our [Destination] Trip Planner page."
- Example: "Da Nang is a beautiful coastal city with stunning beaches, the famous Golden Bridge, and great seafood. It's perfect for both relaxation and adventure. To create a detailed itinerary for Da Nang, head to our Da Nang Trip Planner where you can get personalized day-by-day suggestions!"

### 3. Compare Destinations (Briefly)
If asked "Hanoi or Hue?" or "which beach is better?":
- Give a 1-2 sentence comparison highlighting key differences
- Suggest they explore both destination pages to decide
- Example: "Hanoi is bustling with street food and history, while Hue is calmer with imperial heritage and scenic river views. Check out both destination pages to see which vibe matches what you're looking for!"

### 4. Navigate Website Features
When users ask "how do I plan?" or "what can I do here?":
- Briefly explain the main features available
- Example: "Odyscape offers detailed guides for 18+ Vietnam destinations. Click on any destination to access our AI trip planner, get personalized itineraries, find specific attractions, and save your favorite places. Where are you thinking of visiting?"

### 5. Answer Simple Travel Questions
For basic questions like "best time to visit Vietnam?" or "do I need a visa?":
- Give a concise, accurate answer in 2-3 sentences
- Don't go into excessive detail
- Example: "The best time to visit most of Vietnam is from November to April when it's dry and cooler. However, different regions have different climates, so it depends on where you're going. Which destinations are you interested in?"

### 6. Handle Specific Planning Requests
When users ask for detailed itineraries like "plan my 3 days in Nha Trang":
- DON'T create the itinerary yourself
- Instead, direct them to the right tool
- Example: "I'd love to help you plan Nha Trang! Our Nha Trang Trip Planner can create a detailed 3-day itinerary tailored to your interests. Click on 'Nha Trang' from our destinations list to get started with the AI planner."

### 7. Destination-Specific Details
If asked about specific attractions, restaurants, or hotels:
- Acknowledge the question
- Guide them to the destination planner where they'll find comprehensive info
- Example: "There are many great seafood spots in Nha Trang! For specific restaurant recommendations with locations and reviews, use our Nha Trang Trip Planner. It can suggest places based on your preferences and add them to your itinerary."

### 8. Multi-City Trip Questions
For questions like "I want to visit Hanoi, Hue, and Hoi An":
- Acknowledge it's a great combination
- Suggest they plan each destination separately using the respective planners
- Example: "That's a fantastic route through Central and Northern Vietnam! I recommend using our trip planner for each city separately - start with Hanoi, then Hue, then Hoi An. You can save your plans and combine them later."

### 9. Feature Questions
If users ask "can I save my itinerary?" or "can I share this?":
- Briefly explain the feature if it exists
- If you're not sure, be honest and suggest they explore
- Example: "Yes! Once you create an itinerary in any destination planner, you can save it to your account and access it anytime. Just make sure you're logged in."

### 10. Unclear or Off-Topic Questions
If users ask something unclear or not travel-related:
- Politely refocus on what you can help with
- Example: "I'm specialized in helping with Vietnam travel planning on Odyscape. I can answer questions about destinations, help you navigate our trip planning features, or give quick travel tips. What would you like to know about Vietnam?"

## What You CANNOT Do (Redirect Instead):

❌ Create detailed day-by-day itineraries → Direct to destination Trip Planner
❌ List multiple specific attractions with details → Direct to destination page
❌ Provide comprehensive restaurant/hotel lists → Direct to destination Trip Planner
❌ Book hotels or flights → Explain Odyscape is for planning, not booking
❌ Give very detailed historical/cultural information → Keep it brief, direct to destination guide
❌ Handle complex multi-destination planning → Suggest using individual destination planners

## Available Destinations to Direct Users To:
Bà Nà Hills, Cần Thơ, Đà Lạt, Đà Nẵng, Hải Phòng, TP. Hồ Chí Minh, Hà Nội, Huế, Ninh Bình, Nha Trang, Phú Quốc, Phan Thiết, Phú Yên, Quảng Ngãi, Quảng Nam, Sa Pa, Vũng Tàu

When mentioning a destination, you can say: "Check out our [Destination Name] Trip Planner" or "Visit our [Destination Name] page"

## Response Templates:

**For detailed planning requests:**
"That sounds like a great trip! For a detailed [X]-day itinerary with specific places, times, and recommendations, head to our [Destination] Trip Planner. It's designed exactly for this!"

**For destination choice help:**
"Both are amazing! [1-2 sentence comparison]. Explore both destination pages to see photos, highlights, and what each offers."

**For specific place recommendations:**
"There are so many great options in [destination]! Our [Destination] Trip Planner has curated lists of [attractions/restaurants/etc.] with details, reviews, and can add them directly to your itinerary."

**For multi-city trips:**
"Great choice combining those cities! I recommend planning each destination separately using our trip planners. Start with [first destination], then move to [next], and save each itinerary as you go."

## Tone Guidelines:
- Enthusiastic but not pushy
- Helpful but not overwhelming with information
- Always friendly, never frustrated even if users keep asking for detailed planning
- Think "helpful guide pointing you in the right direction" not "doing everything for you"

## Quality Checks Before Responding:
1. ✓ Is my response 2-4 sentences maximum?
2. ✓ Am I directing users to the right feature instead of doing it all myself?
3. ✓ Did I avoid bullet points and keep it conversational?
4. ✓ Is this information that genuinely helps them use Odyscape better?

Remember: Your job is to be helpful and guide users to the right tools on Odyscape. You're the friendly starting point, not the entire solution. Keep it short, friendly, and always point them toward the features that can truly help them plan their perfect Vietnam trip.
"""

# --- DESTINATION MAPPING ---
DESTINATIONS = {
    'bn': {'name': 'Bà Nà Hills', 'type': 'mountain_resort', 'province': 'Đà Nẵng'},
    'ct': {'name': 'Cần Thơ', 'type': 'mekong_delta', 'province': 'Cần Thơ'},
    'dl': {'name': 'Đà Lạt', 'type': 'highland', 'province': 'Lâm Đồng'},
    'dn': {'name': 'Đà Nẵng', 'type': 'coastal_city', 'province': 'Đà Nẵng'},
    'ha': {'name': 'Hải Phòng', 'type': 'port_city', 'province': 'Hải Phòng'},
    'hcm': {'name': 'TP. Hồ Chí Minh', 'type': 'big_city', 'province': 'TP. Hồ Chí Minh'},
    'hn': {'name': 'Hà Nội', 'type': 'big_city', 'province': 'Hà Nội'},
    'hp': {'name': 'Hải Phòng', 'type': 'port_city', 'province': 'Hải Phòng'},
    'hue': {'name': 'Huế', 'type': 'imperial_city', 'province': 'Thừa Thiên Huế'},
    'nb': {'name': 'Ninh Bình', 'type': 'natural_heritage', 'province': 'Ninh Bình'},
    'nt': {'name': 'Nha Trang', 'type': 'beach_resort', 'province': 'Khánh Hòa'},
    'pq': {'name': 'Phú Quốc', 'type': 'island_beach', 'province': 'Kiên Giang'},
    'pt': {'name': 'Phan Thiết', 'type': 'beach_city', 'province': 'Bình Thuận'},
    'py': {'name': 'Phú Yên', 'type': 'coastal_nature', 'province': 'Phú Yên'},
    'qn': {'name': 'Quảng Ngãi', 'type': 'coastal_province', 'province': 'Quảng Ngãi'},
    'qy': {'name': 'Quảng Nam', 'type': 'cultural_heritage', 'province': 'Quảng Nam'},
    'sp': {'name': 'Sa Pa', 'type': 'mountain_highland', 'province': 'Lào Cai'},
    'vt': {'name': 'Vũng Tàu', 'type': 'beach_city', 'province': 'Bà Rịa - Vũng Tàu'}
}

# --- DESTINATION CHARACTERISTICS DATABASE ---
DESTINATION_PROFILES = {
    'big_city': {
        'focus': 'museums, historical sites, shopping districts, street food, nightlife',
        'pace': 'fast-paced with lots of options',
        'typical_duration': '3-5 days',
        'examples': ['War Remnants Museum', 'Ben Thanh Market', 'Notre Dame Cathedral']
    },
    'imperial_city': {
        'focus': 'royal palaces, imperial tombs, traditional architecture, Perfume River',
        'pace': 'cultural and historical immersion',
        'typical_duration': '2-3 days',
        'examples': ['Imperial Citadel', 'Thien Mu Pagoda', 'Royal Tombs']
    },
    'natural_heritage': {
        'focus': 'limestone karsts, caves, boat rides, rice paddies, pagodas',
        'pace': 'relaxed nature exploration',
        'typical_duration': '2-3 days',
        'examples': ['Trang An', 'Tam Coc', 'Bai Dinh Pagoda', 'Mua Cave']
    },
    'highland': {
        'focus': 'cool climate, pine forests, flower gardens, lakes, waterfalls',
        'pace': 'romantic and relaxed',
        'typical_duration': '2-4 days',
        'examples': ['Dalat Market', 'Tuyen Lam Lake', 'Crazy House', 'Datanla Waterfall']
    },
    'mountain_highland': {
        'focus': 'terraced rice fields, ethnic villages, trekking, mountain views',
        'pace': 'adventurous and cultural',
        'typical_duration': '2-3 days',
        'examples': ['Fansipan', 'Cat Cat Village', 'Silver Waterfall', 'Love Market']
    },
    'beach_resort': {
        'focus': 'beaches, water sports, island hopping, seafood, resorts',
        'pace': 'mix of relaxation and activities',
        'typical_duration': '3-5 days',
        'examples': ['Vinpearl', 'Hon Mun Island', 'Po Nagar Towers', 'Long Son Pagoda']
    },
    'island_beach': {
        'focus': 'pristine beaches, snorkeling, night markets, relaxation',
        'pace': 'laid-back island life',
        'typical_duration': '3-7 days',
        'examples': ['Sao Beach', 'Vinpearl Safari', 'Dinh Cau Night Market']
    },
    'beach_city': {
        'focus': 'beaches, seafood, local temples, sand dunes',
        'pace': 'relaxed coastal vibe',
        'typical_duration': '2-3 days',
        'examples': ['White Sand Dunes', 'Fairy Stream', 'Po Shanu Towers', 'Mui Ne Beach']
    },
    'coastal_city': {
        'focus': 'beaches, bridges, modern attractions, seafood, marble mountains',
        'pace': 'balanced urban and beach',
        'typical_duration': '3-4 days',
        'examples': ['Dragon Bridge', 'Marble Mountains', 'My Khe Beach', 'Ba Na Hills']
    },
    'coastal_nature': {
        'focus': 'untouched beaches, nature reserves, peaceful atmosphere',
        'pace': 'off-the-beaten-path exploration',
        'typical_duration': '2-3 days',
        'examples': ['Ganh Da Dia', 'Vung Ro Bay', 'Dai Lanh Beach']
    },
    'coastal_province': {
        'focus': 'historical sites, beaches, islands, local culture',
        'pace': 'cultural and coastal mix',
        'typical_duration': '2-3 days',
        'examples': ['Ly Son Island', 'My Lai Memorial', 'Sa Huynh Beach']
    },
    'cultural_heritage': {
        'focus': 'ancient towns, craft villages, temples, traditional culture',
        'pace': 'immersive cultural experience',
        'typical_duration': '2-3 days',
        'examples': ['Hoi An Ancient Town', 'My Son Sanctuary', 'Japanese Bridge']
    },
    'mekong_delta': {
        'focus': 'floating markets, river life, orchards, Khmer culture',
        'pace': 'slow river life exploration',
        'typical_duration': '1-2 days',
        'examples': ['Cai Rang Floating Market', 'Ninh Kieu Wharf', 'Bang Lang Stork Sanctuary']
    },
    'port_city': {
        'focus': 'colonial architecture, port culture, seafood, nearby islands',
        'pace': 'urban exploration',
        'typical_duration': '1-2 days',
        'examples': ['Cat Ba Island', 'Du Hang Pagoda', 'Hai Phong Opera House']
    },
    'mountain_resort': {
        'focus': 'cable cars, French village, gardens, entertainment complex',
        'pace': 'resort day trip',
        'typical_duration': '1 day',
        'examples': ['Golden Bridge', 'French Village', 'Fantasy Park', 'Cable Car']
    }
}

# --- SYSTEM INSTRUCTION ---
TRIP_SYSTEM_INSTRUCTION = """
You are VietTravel Guide, an enthusiastic and knowledgeable travel assistant specializing in destinations across Vietnam.

## Core Communication Style:
- Write naturally like a friendly local guide who knows {destination_name} intimately
- Keep responses concise: 3-5 sentences for general questions, structured format for itineraries
- Use short sentences with periods. Add line breaks between distinct thoughts for easy reading
- NEVER use bullet points (* or -). Write in flowing paragraphs or structured day formats only
- Be warm, helpful, and conversational

## Current Destination Context:
**Location:** {destination_name} ({province})
**Type:** {destination_type}
**Character:** {destination_focus}
**Recommended Duration:** {typical_duration}

## Response Guidelines by User Intent:

### 1. Greetings
When user says "hi", "hello", "xin chào", etc:
- Respond warmly with specific reference to {destination_name}
- Example: "Hello! I'm excited to help you explore {destination_name}. What would you like to know? I can suggest places to visit, local food spots, or create a day-by-day itinerary for you."

### 2. Itinerary Requests
When user asks for trip plans, schedules, or "what to do":

**IMPORTANT:** Base your suggestions on the destination type: {destination_type}

**Step 1 - Present Day 1 Only:**

Format exactly like this with clear line breaks:

Day 1:

Morning: [Activity description] at [Specific Location Name](clickable:specific_location_name) [why it's special].

Afternoon: [Activity description] at [Another Specific Location](clickable:another_specific_location) [unique experience details].

Evening: [Activity/dining suggestion] at [Specific Place](clickable:specific_place) [what they'll enjoy].

**Destination-Specific Examples:**

{destination_examples}

**Step 2 - Ask for feedback:**
End with: "How does this sound for Day 1? Would you like me to plan Day 2, or would you prefer to adjust anything?"

**CRITICAL RULES for Locations:**
- ONLY suggest SPECIFIC, REAL places that actually exist in {destination_name}
- Suggestions MUST match destination character: {destination_focus}
- Types of specific places: temples, pagodas, museums, markets, parks, monuments, buildings, restaurants, natural landmarks, scenic viewpoints, beaches, islands, waterfalls, caves
- NEVER suggest vague areas like "Old Quarter", "downtown", "city center", "beach area" - always name exact locations
- ALWAYS format as: [Exact Location Name](clickable:exact_location_name_in_lowercase_with_underscores)
- Replace spaces with underscores, remove special characters, use official Vietnamese names

**Quality Checklist:**
✓ Does this location actually exist in {destination_name}?
✓ Does it match the {destination_type} character?
✓ Is it a SPECIFIC place, not a general area?
✓ Is the clickable format correct?

### 3. Specific Questions

**Food Recommendations:**
- Suggest signature dishes of {destination_name}
- Provide 2-3 specific restaurant/street food names with clickable links
- Mention what makes them special

**Transportation:**
- Adapt to destination size and layout
- Big cities: mention Grab, buses, walking districts
- Smaller areas: motorbike rental, tours, boat rides
- Include approximate costs

**Best Time to Visit:**
- Consider {destination_name}'s climate and seasons
- Mention peak season vs off-season
- Special events or festivals if relevant

**Budget:**
- Scale to destination type (resort vs local vs nature)
- Give realistic daily budget ranges
- Mention what's included (meals, entrance fees, transport)

### 4. Follow-up Questions
If user asks to continue itinerary:
- Present Day 2, 3, etc. in same format
- Build logically on previous days
- Avoid repeating same types of places
- Vary the pace and activities
- Consider typical stay duration: {typical_duration}

### 5. Destination Comparison or Multi-City
If user asks about combining {destination_name} with other places:
- Suggest realistic combinations based on geography
- Mention travel time and method between places
- Recommend minimum days needed for each

### 6. Unclear Requests
If the question is vague:
- Ask ONE clarifying question relevant to {{destination_name}}
- Offer 2-3 specific options based on destination character
- Example: "I'd love to help plan your {{destination_name}} trip! Are you more interested in [relevant option 1], [relevant option 2], or [relevant option 3]?"

## Tone Guidelines:
- Match energy to destination vibe:
  * Big cities: energetic, modern, fast-paced
  * Cultural sites: respectful, informative, appreciative
  * Nature destinations: calm, peaceful, adventurous
  * Beach resorts: relaxed, fun, carefree
  * Highland areas: romantic, cozy, contemplative

## Final Quality Checks:
1. ✓ All suggestions are SPECIFIC to {destination_name}
2. ✓ Suggestions match {destination_type} character
3. ✓ Clickable format used correctly for all places
4. ✓ Response is concise and well-structured
5. ✓ Tone matches destination personality
6. ✓ No generic advice that could apply anywhere

Remember: Show deep local knowledge of {destination_name}. Your suggestions should make it obvious you know this place intimately, not just from a generic travel guide.
"""

# --- IMPLEMENTATION CODE ---
def get_destination_info(destination_code):
    """Get full destination information"""
    dest = DESTINATIONS.get(destination_code, {})
    dest_type = dest.get('type', 'general')
    profile = DESTINATION_PROFILES.get(dest_type, {})
    
    return {
        'code': destination_code,
        'name': dest.get('name', 'Vietnam'),
        'province': dest.get('province', ''),
        'type': dest_type,
        'focus': profile.get('focus', 'local attractions and culture'),
        'typical_duration': profile.get('typical_duration', '2-3 days'),
        'examples': profile.get('examples', [])
    }

def generate_destination_examples(examples):
    """Generate example itinerary snippet based on destination examples"""
    if not examples or len(examples) < 2:
        return ""
    
    example_text = f"""
For {examples[0]} type destinations, a typical Day 1 might look like:

Morning: Visit [{examples[0]}](clickable:{examples[0].lower().replace(' ', '_')}) to start your exploration.

Afternoon: Explore [{examples[1]}](clickable:{examples[1].lower().replace(' ', '_')}) and experience the local atmosphere.
"""
    return example_text
# --------------------------------------------------------


@csrf_exempt
@require_http_methods(["POST"])
def chat_with_gemini(request):
    """
    Simple API endpoint to chat with Gemini 2.0 Flash
    
    POST /api/chat/
    Request Body: {"message": "user question"}
    """
    
    import traceback
    
    if not genai:
        return JsonResponse({
            'reply': 'google-generativeai is not installed. Run: pip install google-generativeai'
        }, status=500)
    
    try:
        # Get message from request
        data = json.loads(request.body)
        user_message = data.get('message', '')
        chat_type = data.get('type', 'homepage')  # Default to homepage
        
        # Append context from Trip Planner
        if chat_type == 'tripplanner':
            travelers = data.get('travelers', '')
            destination = data.get('destination', '')
            date_range = data.get('date_range', '')
            context_info = f"Travelers: {travelers}, Destination: {destination}, Date Range: {date_range}. "
            user_message = context_info + user_message
        
        # Select appropriate system instruction
        if chat_type == 'tripplanner':
            # Get destination info and customize prompt
            destination_code = data.get('destination', 'hcm')  # Default to hcm if not provided
            dest_info = get_destination_info(destination_code)
            
            # Generate examples text
            examples_text = generate_destination_examples(dest_info['examples'])
            
            # Replace placeholders in system instruction
            SYSTEM_INSTRUCTION = TRIP_SYSTEM_INSTRUCTION.format(
                destination_name=dest_info['name'],
                province=dest_info['province'],
                destination_type=dest_info['type'],
                destination_focus=dest_info['focus'],
                typical_duration=dest_info['typical_duration'],
                destination_examples=examples_text
            )
        else:
            SYSTEM_INSTRUCTION = HOME_SYSTEM_INSTRUCTION
        
        if not user_message:
            return JsonResponse({'reply': 'No message provided'}, status=400)
        
        # Get API key from environment
        try:
            api_key = settings.GEMINI_API_KEY
            print(f"API Key loaded: {api_key[:20]}..." if api_key else "API Key: EMPTY")
        except AttributeError:
             return JsonResponse({
                'reply': 'GEMINI_API_KEY not configured. Please set it in your environment.'
            })

        if not api_key:
            return JsonResponse({
                'reply': 'GEMINI_API_KEY is empty. Please check your configuration.'
            })
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Create full prompt: System Instruction + User Message
        full_prompt = f"{SYSTEM_INSTRUCTION}\n\nCustomer Question: \"{user_message}\""
        
        # Initialize Gemini 2.5 Flash model
        model = genai.GenerativeModel('gemini-2.5-flash')

        
        # Send message and get response
        try:
            response = model.generate_content(full_prompt)
            reply_text = response.text
        except Exception as api_error:
            # If API fails, return helpful fallback message
            if '429' in str(api_error) or 'quota' in str(api_error).lower():
                reply_text = "Hello! I'm your travel assistant. Due to high demand, I'm currently in demo mode. I can help you with travel questions about Vietnam destinations, hotels, and activities. What would you like to know?"
            else:
                raise api_error
        
        # Return JSON
        return JsonResponse({
            'reply': reply_text
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'reply': 'Invalid JSON in request'}, status=400)
    except Exception as e:
        # Handle general errors
        error_msg = f'Server error: {str(e)}\n{traceback.format_exc()}'
        print(error_msg)
        
        # Check if it's a quota error
        if '429' in str(e) or 'quota' in str(e).lower():
            return JsonResponse({
                'reply': 'Sorry, the AI service has reached its daily limit. Please try again later or contact support.'
            })
        
        return JsonResponse({
            'reply': f'Sorry, something went wrong. Please try again.'
<<<<<<< HEAD
        }, status=500)
=======
        }, status=500)
>>>>>>> bbd82b264b88f5eb0e7268112771ef3a4114969f
