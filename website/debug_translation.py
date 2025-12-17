import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
import django
django.setup()

from django.test import Client

client = Client()

# Test Vietnamese URL
response_vi = client.get('/vi/input-trip-planner/')
content_vi = response_vi.content.decode('utf-8')

print("Status code:", response_vi.status_code)
print("Content length:", len(content_vi))

# Check for the specific text
if 'Plan a new trip' in content_vi:
    print("❌ Found English text: 'Plan a new trip'")
else:
    print("✅ No English text found")

if 'Lập kế hoạch chuyến đi mới' in content_vi:
    print("✅ Found Vietnamese text: 'Lập kế hoạch chuyến đi mới'")
else:
    print("❌ No Vietnamese text found")

# Check lang attribute
import re
lang_match = re.search(r'lang="([^"]*)"', content_vi)
if lang_match:
    print("HTML lang attribute:", lang_match.group(1))
else:
    print("No lang attribute found")