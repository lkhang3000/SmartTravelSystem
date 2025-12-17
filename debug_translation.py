#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings
from django.test import Client
from django.urls import reverse
from django.utils.translation import activate, get_language

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'website'))
django.setup()

def test_language_detection():
    client = Client()

    print("Testing language detection...")

    # Test English URL
    print("\n1. Testing English URL (/input-trip-planner/):")
    response = client.get('/input-trip-planner/')
    print(f"Status: {response.status_code}")
    print(f"Language: {get_language()}")
    if 'Plan a new trip' in response.content.decode():
        print("✓ Found English text: 'Plan a new trip'")
    else:
        print("✗ English text not found")

    # Test Vietnamese URL
    print("\n2. Testing Vietnamese URL (/vi/input-trip-planner/):")
    from django.urls import resolve
    try:
        resolved = resolve('/vi/input-trip-planner/')
        print(f"Resolved URL: {resolved.url_name}, view: {resolved.func}")
    except Exception as e:
        print(f"URL resolution failed: {e}")
    
    activate('vi')  # Manually activate Vietnamese
    response = client.get('/vi/input-trip-planner/')
    print(f"Status: {response.status_code}")
    print(f"Language after request: {get_language()}")
    content = response.content.decode()
    print(f"Content length: {len(content)}")
    
    # Check the lang attribute
    import re
    lang_match = re.search(r'<html[^>]*lang="([^"]*)"', content)
    if lang_match:
        print(f"HTML lang attribute: '{lang_match.group(1)}'")
    else:
        print("No lang attribute found")
    
    # Look for the heading
    if 'u-text-1' in content:
        print("✓ Found the heading element")
        # Extract the heading content
        match = re.search(r'<h1 class="u-text-1[^"]*"[^>]*>(.*?)</h1>', content, re.DOTALL)
        if match:
            heading_content = match.group(1).strip()
            print(f"Heading content: '{heading_content}'")
    else:
        print("✗ Heading element not found")
    
    # Test direct view call
    print("\n2b. Testing direct view call:")
    from django.test import RequestFactory
    from sightseeing.views import input_trip_planner
    from django.contrib.auth.models import AnonymousUser
    
    factory = RequestFactory()
    request = factory.get('/vi/input-trip-planner/')
    request.user = AnonymousUser()
    activate('vi')
    print(f"Language before view: {get_language()}")
    response = input_trip_planner(request)
    print(f"Response status: {response.status_code}")
    content = response.content.decode()
    print(f"Language after view: {get_language()}")
    
    # Print first 500 characters of content
    print(f"Content preview: {content[:500]}...")
    
    # Check the context variables in the content
    if 'plan_new_trip' in content:
        print("Context variable found in content")
    else:
        print("Context variable NOT found in content")

from django.utils.translation import gettext as _

def test_translation_function():
    print("\n4. Testing translation function directly:")
    activate('en')
    print(f"English: '{_('Plan a new trip')}'")
    activate('vi')
    print(f"Vietnamese: '{_('Plan a new trip')}'")

    # Test if translation is loaded
    from django.utils.translation import trans_real
    translator = trans_real.translation('vi')
    if translator:
        print("✓ Vietnamese translator loaded")
        if hasattr(translator, '_catalog'):
            catalog = translator._catalog
            if 'Plan a new trip' in catalog:
                print(f"✓ Translation found in catalog: '{catalog['Plan a new trip']}'")
            else:
                print("✗ Translation not found in catalog")
    else:
        print("✗ Vietnamese translator not loaded")

if __name__ == '__main__':
    test_language_detection()
    test_translation_function()