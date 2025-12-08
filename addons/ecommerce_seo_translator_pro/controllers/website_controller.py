import logging
import json
from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class SEOAIWebsiteController(http.Controller):

    @http.route(
        '/seo-ai/meta-preview',
        type='json',
        auth='user',
        methods=['POST'],
    )
    def get_meta_preview(self, product_id: int) -> dict:
        """
        Get SERP preview (search engine results page snippet).

        Args:
            product_id: product.template ID

        Returns:
            JSON with meta-tag preview
        """
        try:
            product = request.env['product.template'].browse(product_id)

            if not product.exists():
                return {
                    'success': False,
                    'error': _('Product not found'),
                }

            preview = {
                'success': True,
                'title': product.meta_title or product.name,
                'url': product.get_absolute_url() if hasattr(product, 'get_absolute_url') else f'/shop/p/{product_id}',
                'description': product.meta_description or product.description_sale or '',
                'keywords': product.meta_keywords or '',
                'last_generated': product.seo_last_generated.isoformat() if product.seo_last_generated else None,
            }

            return preview

        except Exception as e:
            _logger.error('[SEO-AI] Error in meta preview: %s', str(e))
            return {
                'success': False,
                'error': str(e),
            }

    @http.route(
        '/seo-ai/batch-generate',
        type='json',
        auth='user',
        methods=['POST'],
    )
    def batch_generate_descriptions(self, product_ids: list, action: str = 'description') -> dict:
        """
        Generate descriptions/meta-tags for multiple products.

        Args:
            product_ids: List of product.template IDs
            action: 'description', 'meta_tags', or 'translate'

        Returns:
            JSON with batch operation status
        """
        try:
            if not request.env.user.has_group('ecommerce_seo_translator_pro.group_ecommerce_seo_ai'):
                return {
                    'success': False,
                    'error': _('Permission denied'),
                }

            products = request.env['product.template'].browse(product_ids)

            if action == 'description':
                products.action_generate_ai_description()
            elif action == 'meta_tags':
                products.action_generate_meta_tags()
            elif action == 'translate':
                products.action_translate_descriptions()
            else:
                return {
                    'success': False,
                    'error': _('Unknown action'),
                }

            _logger.info('[SEO-AI] Batch %s completed for %d products', action, len(product_ids))

            return {
                'success': True,
                'message': _('Batch generation completed for %d products') % len(product_ids),
                'count': len(product_ids),
            }

        except Exception as e:
            _logger.error('[SEO-AI] Batch generation error: %s', str(e))
            return {
                'success': False,
                'error': str(e),
            }

    @http.route(
        '/seo-ai/history',
        type='json',
        auth='user',
        methods=['GET'],
    )
    def get_generation_history(self, product_id: int, limit: int = 10) -> dict:
        """
        Get generation history for a product.

        Args:
            product_id: product.template ID
            limit: Maximum records to return

        Returns:
            JSON with history records
        """
        try:
            history_records = request.env['seo.ai.history'].search(
                [('product_id', '=', product_id)],
                limit=limit,
                order='create_date desc'
            )

            history_data = []
            for record in history_records:
                history_data.append({
                    'id': record.id,
                    'action': record.action,
                    'status': record.status,
                    'create_date': record.create_date.isoformat(),
                    'user': record.user_id.name,
                    'duration_ms': record.duration_ms,
                })

            return {
                'success': True,
                'history': history_data,
                'count': len(history_data),
            }

        except Exception as e:
            _logger.error('[SEO-AI] Error retrieving history: %s', str(e))
            return {
                'success': False,
                'error': str(e),
            }

    @http.route(
        '/seo-ai/config',
        type='json',
        auth='user',
        methods=['GET'],
    )
    def get_config(self) -> dict:
        """
        Get module configuration (for frontend).

        Returns:
            JSON with configuration
        """
        try:
            if not request.env.user.has_group('ecommerce_seo_translator_pro.group_ecommerce_seo_ai'):
                return {
                    'success': False,
                    'error': _('Permission denied'),
                }

            params = request.env['ir.config_parameter'].sudo()

            return {
                'success': True,
                'batch_enabled': params.get_param('ecommerce_seo_translator_pro.batch_enabled', 'True') == 'True',
                'async_enabled': params.get_param('ecommerce_seo_translator_pro.async_enabled', 'False') == 'True',
                'default_tone': params.get_param('ecommerce_seo_translator_pro.default_tone', 'professional'),
            }

        except Exception as e:
            _logger.error('[SEO-AI] Error retrieving config: %s', str(e))
            return {
                'success': False,
                'error': str(e),
            }
