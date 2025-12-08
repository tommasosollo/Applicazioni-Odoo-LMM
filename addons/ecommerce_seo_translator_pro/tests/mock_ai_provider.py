"""Mock AI Provider for testing without OpenAI API."""

import json
from typing import Dict, List, Optional


class MockAIProvider:
    """Mock provider that returns deterministic responses for testing."""

    @staticmethod
    def generate_description(
        product_name: str,
        description: str,
        tone: str = 'professional',
        word_count: int = 200,
        keywords: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        """Mock description generation."""
        return {
            'description': f'''<p>Discover the exceptional {product_name}. 
            This premium product offers outstanding performance and reliability. 
            Designed with precision and crafted with excellence. 
            {description}</p>
            <ul>
            <li>High quality construction</li>
            <li>Professional design</li>
            <li>Excellent value for money</li>
            </ul>''',
            'bullets': [
                'High quality construction',
                'Professional design',
                'Excellent value for money',
                'Long-lasting durability',
            ],
            'meta_title': f'{product_name} - Premium Quality',
            'meta_description': f'Discover the exceptional {product_name}. Professional design and outstanding performance.',
        }

    @staticmethod
    def translate_text(
        text: str,
        source_lang: str,
        target_lang: str,
        glossary: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """Mock translation."""
        translation_map = {
            ('en', 'it'): {
                'product': 'prodotto',
                'high quality': 'alta qualità',
                'premium': 'premium',
                'design': 'design',
            },
            ('en', 'es'): {
                'product': 'producto',
                'high quality': 'alta calidad',
                'premium': 'premium',
                'design': 'diseño',
            },
        }

        lang_pair = (source_lang, target_lang)
        glossary_dict = translation_map.get(lang_pair, {})

        if glossary:
            glossary_dict.update(glossary)

        translated = text
        for original, replacement in glossary_dict.items():
            translated = translated.replace(original, replacement)

        return {
            'translation': translated,
        }

    @staticmethod
    def generate_meta_tags(
        product_name: str,
        description: str,
        keywords: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """Mock meta-tags generation."""
        keywords_list = keywords or ['product', 'quality', 'design']
        keywords_str = ', '.join(keywords_list[:5])

        return {
            'meta_title': f'{product_name} - Premium Quality | Shop Now',
            'meta_description': f'{description[:150]}...',
            'meta_keywords': keywords_str,
        }


class MockOpenAIClient:
    """Mock OpenAI client for testing."""

    def __init__(self, api_key: str = 'sk-mock-test'):
        self.api_key = api_key

    def chat_completions_create(self, **kwargs):
        """Mock chat completions."""
        messages = kwargs.get('messages', [])
        content = messages[0]['content'] if messages else ''

        response_content = json.dumps({
            'description': '<p>Mock generated description</p>',
            'bullets': ['Feature 1', 'Feature 2'],
            'meta_title': 'Mock Title',
            'meta_description': 'Mock description',
            'meta_keywords': 'mock, test, product',
        })

        class MockMessage:
            def __init__(self, content):
                self.content = content

        class MockChoice:
            def __init__(self, message):
                self.message = message

        class MockResponse:
            def __init__(self, content):
                self.choices = [MockChoice(MockMessage(content))]

        return MockResponse(response_content)
