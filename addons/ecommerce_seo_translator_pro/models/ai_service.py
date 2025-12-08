import logging
import json
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    from openai import OpenAI, RateLimitError, APIError
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

_logger = logging.getLogger(__name__)


class AISEOService(models.TransientModel):

    _name = 'ai.seo.service'
    _description = 'AI SEO Service - Text generation, translation, and meta-tags'

    _circuit_breaker = {
        'failed_count': 0,
        'last_failure_time': None,
        'is_open': False,
    }
    _rate_limit_data = {}

    @api.model
    def _get_client(self) -> Optional[OpenAI]:
        """
        Get OpenAI client with API key from configuration.

        Returns:
            OpenAI: Configured OpenAI client, or None if not configured
        """
        if not HAS_OPENAI:
            _logger.error('[SEO-AI] OpenAI library not installed')
            return None

        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'ecommerce_seo_translator_pro.openai_api_key', ''
        )

        if not api_key:
            _logger.warning('[SEO-AI] OpenAI API key not configured')
            return None

        return OpenAI(api_key=api_key)

    def _check_circuit_breaker(self) -> bool:
        """
        Check if circuit breaker is open (too many failures).

        Returns:
            bool: True if circuit is open (fail fast), False if operational
        """
        if not self._circuit_breaker['is_open']:
            return False

        last_failure = self._circuit_breaker['last_failure_time']
        if not last_failure:
            return False

        timeout_minutes = 5
        if datetime.now() - last_failure > timedelta(minutes=timeout_minutes):
            self._circuit_breaker['is_open'] = False
            self._circuit_breaker['failed_count'] = 0
            _logger.info('[SEO-AI] Circuit breaker reset')
            return False

        return True

    def _record_failure(self) -> None:
        """Record a failure and update circuit breaker state."""
        self._circuit_breaker['failed_count'] += 1
        self._circuit_breaker['last_failure_time'] = datetime.now()

        if self._circuit_breaker['failed_count'] >= 5:
            self._circuit_breaker['is_open'] = True
            _logger.error(
                '[SEO-AI] Circuit breaker opened after %d failures',
                self._circuit_breaker['failed_count']
            )

    def _check_rate_limit(self, user_id: int) -> bool:
        """
        Check if user has exceeded rate limit (5 requests per minute).

        Args:
            user_id: Odoo user ID

        Returns:
            bool: True if rate limit exceeded, False if allowed
        """
        now = time.time()
        user_key = f'user_{user_id}'

        if user_key not in self._rate_limit_data:
            self._rate_limit_data[user_key] = []

        requests = self._rate_limit_data[user_key]
        requests = [req_time for req_time in requests if now - req_time < 60]

        if len(requests) >= 5:
            _logger.warning(
                '[SEO-AI] Rate limit exceeded for user %d',
                user_id
            )
            return True

        requests.append(now)
        self._rate_limit_data[user_key] = requests
        return False

    def generate_description(
        self,
        product,
        tone: str = 'professional',
        word_count: int = 200,
        keywords: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        """
        Generate SEO-optimized product description using AI.

        Args:
            product: product.template record
            tone: Writing tone ('professional', 'casual', 'technical')
            word_count: Target word count (150-250)
            keywords: List of keywords to incorporate

        Returns:
            Dict with keys:
                - success: bool
                - description: str (generated HTML)
                - meta_title: str
                - meta_description: str
                - bullets: List[str]
                - raw_response: str
                - error: str (if failed)
        """
        result = {
            'success': False,
            'description': '',
            'meta_title': '',
            'meta_description': '',
            'bullets': [],
            'raw_response': '',
            'error': '',
        }

        if self._check_circuit_breaker():
            result['error'] = _('AI service temporarily unavailable due to repeated failures. Please try again later.')
            return result

        if self._check_rate_limit(self.env.user.id):
            result['error'] = _('Rate limit exceeded. Maximum 5 requests per minute.')
            return result

        client = self._get_client()
        if not client:
            result['error'] = _('OpenAI API key not configured.')
            return result

        try:
            prompt = self._build_description_prompt(
                product, tone, word_count, keywords
            )

            _logger.info('[SEO-AI] Calling OpenAI API for description generation')

            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.7,
                max_tokens=1000,
                timeout=30,
            )

            raw_response = response.choices[0].message.content
            result['raw_response'] = raw_response

            parsed = self._parse_description_response(raw_response)
            result.update(parsed)
            result['success'] = True

            self._record_success()

            _logger.info('[SEO-AI] Description generation successful for product %d', product.id)

        except RateLimitError as e:
            _logger.warning('[SEO-AI] OpenAI rate limit: %s', str(e))
            result['error'] = _('OpenAI API rate limit exceeded. Please try again in a few minutes.')
            self._record_failure()

        except APIError as e:
            _logger.error('[SEO-AI] OpenAI API error: %s', str(e))
            result['error'] = _('Error communicating with OpenAI API.')
            self._record_failure()

        except Exception as e:
            _logger.error('[SEO-AI] Unexpected error in description generation: %s', str(e))
            result['error'] = _('Unexpected error during generation.')
            self._record_failure()

        return result

    def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        glossary: Optional[Dict[str, str]] = None,
    ) -> Dict[str, any]:
        """
        Translate text while respecting glossary and brand style.

        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en')
            target_lang: Target language code (e.g., 'it')
            glossary: Dict of terms to preserve {'term_en': 'term_lang'}

        Returns:
            Dict with:
                - success: bool
                - translation: str
                - raw_response: str
                - error: str (if failed)
        """
        result = {
            'success': False,
            'translation': '',
            'raw_response': '',
            'error': '',
        }

        if self._check_circuit_breaker():
            result['error'] = _('AI service temporarily unavailable.')
            return result

        if self._check_rate_limit(self.env.user.id):
            result['error'] = _('Rate limit exceeded.')
            return result

        client = self._get_client()
        if not client:
            result['error'] = _('OpenAI API key not configured.')
            return result

        if not glossary:
            glossary = {}

        try:
            prompt = self._build_translation_prompt(
                text, source_lang, target_lang, glossary
            )

            _logger.info('[SEO-AI] Calling OpenAI API for translation')

            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.3,
                max_tokens=2000,
                timeout=30,
            )

            translation = response.choices[0].message.content.strip()
            result['success'] = True
            result['translation'] = translation
            result['raw_response'] = translation

            self._record_success()

            _logger.info('[SEO-AI] Translation successful')

        except (RateLimitError, APIError) as e:
            _logger.error('[SEO-AI] OpenAI error during translation: %s', str(e))
            result['error'] = _('Error communicating with OpenAI API.')
            self._record_failure()

        except Exception as e:
            _logger.error('[SEO-AI] Unexpected error in translation: %s', str(e))
            result['error'] = _('Unexpected error during translation.')
            self._record_failure()

        return result

    def generate_meta_tags(self, product) -> Dict[str, any]:
        """
        Generate SEO meta-tags (title, description, keywords).

        Args:
            product: product.template record

        Returns:
            Dict with:
                - success: bool
                - meta_title: str (max 60 chars)
                - meta_description: str (max 160 chars)
                - meta_keywords: str (comma-separated, max 200 chars)
                - raw_response: str
                - error: str (if failed)
        """
        result = {
            'success': False,
            'meta_title': '',
            'meta_description': '',
            'meta_keywords': '',
            'raw_response': '',
            'error': '',
        }

        if self._check_circuit_breaker():
            result['error'] = _('AI service temporarily unavailable.')
            return result

        if self._check_rate_limit(self.env.user.id):
            result['error'] = _('Rate limit exceeded.')
            return result

        client = self._get_client()
        if not client:
            result['error'] = _('OpenAI API key not configured.')
            return result

        try:
            prompt = self._build_meta_tags_prompt(product)

            _logger.info('[SEO-AI] Calling OpenAI API for meta-tags generation')

            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.7,
                max_tokens=500,
                timeout=30,
            )

            raw_response = response.choices[0].message.content
            result['raw_response'] = raw_response

            parsed = self._parse_meta_tags_response(raw_response)
            result.update(parsed)
            result['success'] = True

            self._record_success()

            _logger.info('[SEO-AI] Meta-tags generation successful')

        except (RateLimitError, APIError) as e:
            _logger.error('[SEO-AI] OpenAI error during meta-tags generation: %s', str(e))
            result['error'] = _('Error communicating with OpenAI API.')
            self._record_failure()

        except Exception as e:
            _logger.error('[SEO-AI] Unexpected error in meta-tags generation: %s', str(e))
            result['error'] = _('Unexpected error during meta-tags generation.')
            self._record_failure()

        return result

    def _build_description_prompt(
        self,
        product,
        tone: str,
        word_count: int,
        keywords: Optional[List[str]],
    ) -> str:
        """Build the prompt for description generation."""
        keywords_text = ', '.join(keywords) if keywords else 'not specified'

        prompt = f"""You are a professional e-commerce copywriter specializing in SEO-optimized product descriptions.

Generate an SEO-optimized product description for this product:

**Product Name**: {product.name}
**Category**: {product.categ_id.name if product.categ_id else 'Not specified'}
**Current Description**: {product.description or 'Not provided'}
**Technical Specifications**: {product.description_sale or 'Not provided'}

**Requirements**:
1. Write in {tone} tone
2. Target word count: {word_count} words
3. Incorporate these keywords naturally: {keywords_text}
4. Make it persuasive and action-oriented
5. Focus on customer benefits, not just features
6. Include a compelling call-to-action
7. Optimize for search engines (natural keyword placement)

**Output Format** (JSON):
{{
    "description": "Main product description (HTML formatted with <p>, <ul>, <li>)",
    "bullets": ["Benefit 1", "Benefit 2", "Benefit 3", "Benefit 4"],
    "meta_title": "SEO title (max 60 chars)",
    "meta_description": "SEO meta description (max 160 chars)"
}}

Generate the description now:"""
        return prompt

    def _parse_description_response(self, response: str) -> Dict[str, any]:
        """Parse JSON response from description generation."""
        try:
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]

            data = json.loads(cleaned)

            return {
                'description': data.get('description', ''),
                'bullets': data.get('bullets', []),
                'meta_title': data.get('meta_title', '')[:60],
                'meta_description': data.get('meta_description', '')[:160],
            }

        except json.JSONDecodeError:
            _logger.warning('[SEO-AI] Failed to parse description response as JSON')
            return {
                'description': response,
                'bullets': [],
                'meta_title': '',
                'meta_description': '',
            }

    def _build_translation_prompt(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        glossary: Dict[str, str],
    ) -> str:
        """Build the prompt for translation."""
        glossary_text = '\n'.join(
            [f"- {src}: {tgt}" for src, tgt in glossary.items()]
        ) if glossary else "None"

        prompt = f"""Translate this e-commerce product text from {source_lang} to {target_lang}.

**Text to translate**:
{text}

**Glossary** (must be preserved exactly):
{glossary_text}

**Requirements**:
1. Preserve all terms in the glossary
2. Maintain professional tone for e-commerce
3. Keep HTML tags unchanged
4. Keep SEO context intact
5. Do NOT add explanations, only provide the translation

Translation:"""
        return prompt

    def _build_meta_tags_prompt(self, product) -> str:
        """Build the prompt for meta-tags generation."""
        prompt = f"""Generate SEO-optimized meta-tags for this product:

**Product Name**: {product.name}
**Category**: {product.categ_id.name if product.categ_id else 'Unknown'}
**Description**: {product.description or 'Not available'}

**Output Format** (JSON):
{{
    "meta_title": "Compelling SEO title (max 60 characters)",
    "meta_description": "Engaging meta description (max 160 characters)",
    "meta_keywords": "keyword1, keyword2, keyword3, keyword4, keyword5"
}}

**Requirements**:
- Meta title: Include main keyword, max 60 chars
- Meta description: Action-oriented, max 160 chars, include main keyword
- Meta keywords: 3-5 most relevant keywords

Generate the meta-tags:"""
        return prompt

    def _parse_meta_tags_response(self, response: str) -> Dict[str, any]:
        """Parse JSON response from meta-tags generation."""
        try:
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]

            data = json.loads(cleaned)

            return {
                'meta_title': data.get('meta_title', '')[:60],
                'meta_description': data.get('meta_description', '')[:160],
                'meta_keywords': data.get('meta_keywords', '')[:200],
            }

        except json.JSONDecodeError:
            _logger.warning('[SEO-AI] Failed to parse meta-tags response as JSON')
            return {
                'meta_title': '',
                'meta_description': '',
                'meta_keywords': '',
            }

    def _record_success(self) -> None:
        """Reset failure counters on successful request."""
        self._circuit_breaker['failed_count'] = 0
        self._circuit_breaker['last_failure_time'] = None
