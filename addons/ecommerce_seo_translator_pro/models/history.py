"""
SEO AI History Model - Audit Trail for AI Operations

Records all AI-powered SEO operations for audit, compliance, and analytics:
- Description generation attempts (success/failure)
- Translation operations per language
- Meta-tags generation
- User actions and timestamps
- GDPR-compliant input hashing

Automatically tracks:
- Who performed the action (user_id)
- When it happened (create_date)
- What the result was (output)
- Execution time and estimated API cost
"""

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SEOAIHistory(models.Model):
    """
    SEO AI History Model - Complete audit trail for AI operations.
    
    Stores records of all AI-powered content generation and translation.
    Ordered by creation date (newest first) for easy review.
    """

    _name = 'seo.ai.history'
    _description = 'SEO AI Generation History'
    _order = 'create_date desc'
    _rec_name = 'action'

    product_id = fields.Many2one(
        'product.template',
        string=_('Product'),
        required=True,
        ondelete='cascade',
    )

    action = fields.Selection(
        selection=[
            ('description_generation', _('Description Generation')),
            ('translation', _('Translation')),
            ('meta_tags_generation', _('Meta-Tags Generation')),
            ('content_confirmation', _('Content Confirmation & Publication')),
        ],
        string=_('Action'),
        required=True,
    )

    status = fields.Selection(
        selection=[
            ('success', _('Success')),
            ('error', _('Error')),
            ('pending', _('Pending')),
        ],
        string=_('Status'),
        default='pending',
    )

    input_hash = fields.Char(
        string=_('Input Hash (GDPR)'),
        help=_('SHA256 hash of input for privacy'),
    )

    output = fields.Text(
        string=_('Output / Result'),
        help=_('Generated content or error message'),
    )

    user_id = fields.Many2one(
        'res.users',
        string=_('User'),
        default=lambda self: self.env.user,
        readonly=True,
    )

    target_language = fields.Char(
        string=_('Target Language'),
        help=_('Target language for translations'),
    )

    duration_ms = fields.Integer(
        string=_('Duration (milliseconds)'),
        help=_('Execution time in milliseconds'),
    )

    api_call_cost = fields.Float(
        string=_('API Call Cost (USD)'),
        help=_('Estimated cost from OpenAI API'),
    )

    create_date = fields.Datetime(
        string=_('Creation Date'),
        readonly=True,
    )

    def unlink(self):
        """
        Delete history records.

        Only system managers can delete history records for audit compliance.
        Regular users cannot delete audit trail records.
        
        Raises:
            UserError: If user is not a system administrator
        """
        if not self.env.user.has_group('base.group_system'):
            raise UserError(_('Only managers can delete history'))

        return super().unlink()

    @api.model
    def get_stats_by_product(self, product_id: int) -> dict:
        """
        Get statistics for a product's AI operations.

        Aggregates all AI operations performed on a product and returns
        success/failure counts by action type.

        Args:
            product_id: Product template ID

        Returns:
            Dict with:
                - total_actions: Total number of operations
                - successful: Count of successful operations
                - errors: Count of failed operations
                - by_action: Dict with stats per action type
        """
        records = self.search([
            ('product_id', '=', product_id),
        ])

        stats = {
            'total_actions': len(records),
            'successful': len(records.filtered(lambda r: r.status == 'success')),
            'errors': len(records.filtered(lambda r: r.status == 'error')),
            'by_action': {},
        }

        for action_type in ['description_generation', 'translation', 'meta_tags_generation']:
            action_records = records.filtered(lambda r: r.action == action_type)
            stats['by_action'][action_type] = {
                'total': len(action_records),
                'successful': len(action_records.filtered(lambda r: r.status == 'success')),
                'errors': len(action_records.filtered(lambda r: r.status == 'error')),
            }

        return stats

    @api.model
    def cleanup_old_records(self, days: int = 90) -> int:
        """
        Delete history records older than specified days.

        Scheduled cleanup task to remove old audit records and manage
        database storage. Can be scheduled as a cron job.

        Args:
            days: Number of days to keep in history (default 90)

        Returns:
            int: Number of deleted records

        Example:
            self.env['seo.ai.history'].cleanup_old_records(days=60)
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=days)

        old_records = self.search([
            ('create_date', '<', cutoff_date),
        ])

        count = len(old_records)
        old_records.unlink()

        _logger.info('[SEO-AI] Cleaned up %d history records older than %d days', count, days)

        return count
