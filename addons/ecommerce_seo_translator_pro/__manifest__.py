{
    'name': 'E-Commerce SEO Translator Pro',
    'version': '19.0.1.0.0',
    'category': 'E-Commerce',
    'summary': 'AI-powered SEO description generation, translation, and meta-tag creation for products',
    'description': '''
        E-Commerce SEO Translator Pro

        Generate SEO-optimized product descriptions, automatic translations with glossary support,
        and meta-tag creation using AI. Features include:

        • AI-powered description generation (150-250 words, SEO optimized)
        • Contextual translation with custom glossary
        • Automatic meta-tag generation (title, description, keywords)
        • SERP preview snippets
        • Rate limiting and resilience (retry, backoff, circuit breaker)
        • Async/Queue job support
        • Full audit trail
        • GDPR compliant

        Compatible with Odoo 19 and OWL 2.
    ''',
    'author': 'AI-Odoo Development',
    'license': 'LGPL-3',
    'depends': [
        'product',
        'website',
        'website_sale',
        'base',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/glossary_views.xml',
        'views/website_templates.xml',
        'data/demo_data.xml',
        'data/seo_cron_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'external_dependencies': {
        'python': [
            'openai>=1.0.0',
            'tenacity>=8.0.0',
        ],
    },
    'assets': {
        'web.assets_backend': [
            'ecommerce_seo_translator_pro/static/src/js/seo_preview.js',
        ],
    },
}
