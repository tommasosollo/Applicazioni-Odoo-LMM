#!/usr/bin/env python3
import xml.etree.ElementTree as ET

try:
    ET.parse('addons/ecommerce_seo_translator_pro/views/product_template_views.xml')
    print('✓ XML is valid')
except Exception as e:
    print(f'✗ XML validation failed: {e}')
    exit(1)
