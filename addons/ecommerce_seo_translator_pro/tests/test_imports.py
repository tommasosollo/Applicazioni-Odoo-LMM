#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

try:
    from addons.ecommerce_seo_translator_pro.models import ai_service
    print('✓ ai_service imports successfully')
except Exception as e:
    print(f'✗ ai_service import failed: {e}')
    sys.exit(1)

try:
    from addons.ecommerce_seo_translator_pro.models import product_template
    print('✓ product_template imports successfully')
except Exception as e:
    print(f'✗ product_template import failed: {e}')
    sys.exit(1)

print('All imports successful!')
