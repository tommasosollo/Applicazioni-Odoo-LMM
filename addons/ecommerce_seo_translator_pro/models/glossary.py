"""
SEO AI Glossary Model - Translation Terminology Management

Maintains a controlled vocabulary for product translations to ensure
consistency of technical terms, brand names, and marketing language
across all languages.

Features:
- Per-language term mappings
- Category-based organization (Product, Technical, Marketing, Brand)
- Uniqueness constraints to prevent duplicate terms per language
- Active/Inactive toggle for term lifecycle management
"""

import logging
from typing import Dict
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class SEOAIGlossary(models.Model):
    """
    SEO AI Glossary Model - Technical terminology management.
    
    Maintains translation glossaries to ensure brand consistency and
    technical accuracy when translating product descriptions.
    Ordered by language and term alphabetically.
    """

    _name = 'seo.ai.glossary'
    _description = 'SEO AI Glossary - Technical terms for translation'
    _order = 'language_code, term asc'

    term = fields.Char(
        string=_('English Term'),
        required=True,
        help=_('Original English term'),
    )

    translation = fields.Char(
        string=_('Translation'),
        required=True,
        help=_('Translated term'),
    )

    language_code = fields.Char(
        string=_('Language Code'),
        required=True,
        help=_('Target language code (e.g., it, es, fr)'),
    )

    category = fields.Selection(
        selection=[
            ('product', _('Product')),
            ('technical', _('Technical')),
            ('marketing', _('Marketing')),
            ('brand', _('Brand')),
        ],
        string=_('Category'),
        default='product',
    )

    notes = fields.Text(
        string=_('Notes'),
        help=_('Usage notes or context'),
    )

    active = fields.Boolean(
        string=_('Active'),
        default=True,
    )

    _sql_constraints = [
        (
            'unique_term_language',
            'unique(term, language_code)',
            _('This term already exists for this language'),
        ),
    ]

    @api.model
    def _get_glossary_for_language(self, language_code: str) -> Dict[str, str]:
        """
        Get glossary dictionary for a specific language.

        Retrieves all active glossary entries for the specified language
        and returns them as a simple dict for easy lookups during translation.

        Args:
            language_code: Language code (e.g., 'it_IT', 'es_ES', 'en_US')

        Returns:
            Dict mapping English terms (keys) to translations (values)
            Empty dict if no glossary entries exist for that language
        """
        glossary_records = self.search([
            ('language_code', '=', language_code),
            ('active', '=', True),
        ])

        glossary_dict = {}
        for record in glossary_records:
            glossary_dict[record.term] = record.translation

        _logger.info(
            '[SEO-AI] Loaded %d glossary terms for language %s',
            len(glossary_dict), language_code
        )

        return glossary_dict

    @api.model
    def _get_all_glossaries(self) -> Dict[str, Dict[str, str]]:
        """
        Get all glossaries organized by language.

        Returns nested dictionary for efficient multi-language operations.
        Useful for bulk translation operations or generating reports.

        Returns:
            Dict with structure: {
                'it_IT': {'term1': 'translation1', 'term2': 'translation2'},
                'es_ES': {'term1': 'traduccion1', ...},
                ...
            }
        """
        glossary_records = self.search([('active', '=', True)])

        glossaries = {}
        for record in glossary_records:
            if record.language_code not in glossaries:
                glossaries[record.language_code] = {}

            glossaries[record.language_code][record.term] = record.translation

        return glossaries
