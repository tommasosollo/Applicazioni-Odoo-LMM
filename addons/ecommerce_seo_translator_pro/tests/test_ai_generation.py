import logging
from unittest.mock import patch, MagicMock
from odoo.tests import TransactionCase
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TestAISEOGeneration(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'Test Product',
            'description': 'A test product for SEO AI generation',
            'description_sale': 'Premium test product with excellent features',
            'list_price': 99.99,
        })

    def test_01_glossary_creation(self):
        glossary = self.env['seo.ai.glossary'].create({
            'term': 'warranty',
            'translation': 'garanzia',
            'language_code': 'it',
            'category': 'product',
        })

        self.assertTrue(glossary.id)
        self.assertEqual(glossary.term, 'warranty')
        self.assertEqual(glossary.translation, 'garanzia')

    def test_02_glossary_for_language(self):
        self.env['seo.ai.glossary'].create({
            'term': 'product',
            'translation': 'prodotto',
            'language_code': 'it',
            'category': 'product',
        })

        glossary_dict = self.env['seo.ai.glossary']._get_glossary_for_language('it')
        self.assertIn('product', glossary_dict)
        self.assertEqual(glossary_dict['product'], 'prodotto')

    def test_03_history_creation(self):
        history = self.env['seo.ai.history'].create({
            'product_id': self.product.id,
            'action': 'description_generation',
            'status': 'success',
            'output': 'Generated description',
            'user_id': self.env.user.id,
        })

        self.assertTrue(history.id)
        self.assertEqual(history.status, 'success')

    def test_04_product_hash_input(self):
        hashed = self.product._hash_input('test content')
        self.assertEqual(len(hashed), 64)

    def test_05_meta_tags_validation(self):
        self.product.write({
            'meta_title': 'Test Title',
            'meta_description': 'Test Description',
            'meta_keywords': 'test, keywords',
        })

        self.assertEqual(self.product.meta_title, 'Test Title')
        self.assertEqual(self.product.meta_description, 'Test Description')

    def test_06_circuit_breaker(self):
        service = self.env['ai.seo.service']

        self.assertFalse(service._check_circuit_breaker())

        for _ in range(5):
            service._record_failure()

        self.assertTrue(service._check_circuit_breaker())

    def test_07_rate_limiting(self):
        service = self.env['ai.seo.service']
        user_id = self.env.user.id

        for i in range(4):
            self.assertFalse(service._check_rate_limit(user_id))

        self.assertTrue(service._check_rate_limit(user_id))

    @patch('ecommerce_seo_translator_pro.models.ai_service.OpenAI')
    def test_08_description_generation_mock(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''
        {
            "description": "<p>Test description</p>",
            "bullets": ["Feature 1", "Feature 2"],
            "meta_title": "Test Product",
            "meta_description": "Test description"
        }
        '''
        mock_client.chat.completions.create.return_value = mock_response

        self.env['ir.config_parameter'].sudo().set_param(
            'ecommerce_seo_translator_pro.openai_api_key', 'sk-test'
        )

        service = self.env['ai.seo.service']
        result = service.generate_description(self.product)

        self.assertTrue(result['success'])
        self.assertIn('description', result)

    @patch('ecommerce_seo_translator_pro.models.ai_service.OpenAI')
    def test_09_translation_mock(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices[0].message.content = 'Descrizione tradotta'
        mock_client.chat.completions.create.return_value = mock_response

        self.env['ir.config_parameter'].sudo().set_param(
            'ecommerce_seo_translator_pro.openai_api_key', 'sk-test'
        )

        service = self.env['ai.seo.service']
        result = service.translate_text(
            'Test description',
            source_lang='en',
            target_lang='it'
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['translation'], 'Descrizione tradotta')

    def test_10_history_stats(self):
        for _ in range(3):
            self.env['seo.ai.history'].create({
                'product_id': self.product.id,
                'action': 'description_generation',
                'status': 'success',
            })

        stats = self.env['seo.ai.history'].get_stats_by_product(self.product.id)

        self.assertGreaterEqual(stats['total_actions'], 3)
        self.assertGreaterEqual(stats['successful'], 3)
