import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')
import django
django.setup()

from django.template import Template, Context
from django.utils.translation import activate

# Test template rendering
template_str = '{% load i18n %}{% trans "Plan a new trip" %}'
template = Template(template_str)

# English
activate('en')
context = Context({})
result_en = template.render(context)
print('English result:', repr(result_en))

# Vietnamese
activate('vi')
context = Context({})
result_vi = template.render(context)
print('Vietnamese result:', repr(result_vi))