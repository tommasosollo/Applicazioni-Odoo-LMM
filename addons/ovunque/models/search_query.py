import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except ImportError:
    _logger.warning("openai library not installed")


class SearchQuery(models.Model):
    _name = 'search.query'
    _description = 'Natural Language Search Query'
    _order = 'create_date desc'

    AVAILABLE_MODELS = [
        ('res.partner', 'Partner / Contact'),
        ('account.move', 'Invoice'),
        ('product.product', 'Product Variant'),
        ('product.template', 'Product Template'),
        ('sale.order', 'Sales Order'),
        ('purchase.order', 'Purchase Order'),
        ('stock.move', 'Stock Move'),
        ('crm.lead', 'CRM Lead'),
        ('project.task', 'Project Task'),
    ]
    
    CATEGORY_MODELS = {
        'customers': ['res.partner'],
        'suppliers': ['res.partner'],
        'partners': ['res.partner'],
        'invoices': ['account.move'],
        'bills': ['account.move'],
        'documents': ['account.move'],
        'products': ['product.template', 'product.product'],
        'inventory': ['stock.move', 'product.template'],
        'orders': ['sale.order', 'purchase.order'],
        'sales': ['sale.order'],
        'purchases': ['purchase.order'],
        'crm': ['crm.lead'],
        'opportunities': ['crm.lead'],
        'tasks': ['project.task'],
        'projects': ['project.task'],
    }

    name = fields.Char('Query Text', required=True)
    category = fields.Selection([
        ('customers', 'Clienti / Contatti'),
        ('products', 'Prodotti'),
        ('invoices', 'Fatture e Documenti'),
        ('orders', 'Ordini'),
        ('crm', 'CRM / Opportunità'),
        ('tasks', 'Task Progetto'),
    ], 'Categoria', required=True, default='customers')
    model_name = fields.Selection(AVAILABLE_MODELS, 'Modello Specifico', readonly=True)
    model_domain = fields.Text('Generated Domain')
    results_count = fields.Integer('Results Count')
    raw_response = fields.Text('Raw LLM Response')
    result_ids = fields.One2many('search.result', 'query_id', 'Results')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('success', 'Success'),
        ('error', 'Error'),
    ], default='draft')
    error_message = fields.Text('Error Message')
    created_by_user = fields.Many2one('res.users', 'Created By', default=lambda self: self.env.user)

    def action_execute_search(self):
        """Execute the natural language search"""
        for record in self:
            try:
                record.result_ids.unlink()
                
                if not record.category:
                    raise UserError(_('Please select a category (Clienti, Prodotti, etc.) before searching.'))
                
                available_models = self.CATEGORY_MODELS.get(record.category, ['res.partner'])
                
                valid_model = None
                for model in available_models:
                    try:
                        self.env[model]
                        valid_model = model
                        break
                    except KeyError:
                        _logger.warning(f"[CHECK] Model {model} not installed")
                        continue
                
                if not valid_model:
                    category_label = dict(record._fields['category'].selection).get(record.category, record.category)
                    error_msg = _(
                        'The required module for "%s" is not installed.\n\n'
                        'To enable this feature:\n'
                        '1. Go to Apps in Odoo\n'
                        '2. Search for the module (e.g., "CRM", "Sales", "Inventory")\n'
                        '3. Click "Install"\n'
                        '4. Come back and try again\n\n'
                        'Technical: Missing modules: %s'
                    ) % (category_label, ', '.join(available_models))
                    raise UserError(error_msg)
                
                record.model_name = valid_model
                _logger.warning(f"[SELECT] Category {record.category} → Model {valid_model}")
                
                domain = record._parse_natural_language()
                record.model_domain = str(domain)
                record.status = 'success'
                
                Model = self.env[record.model_name]
                results = Model.search(domain)
                record.results_count = len(results)
                
                result_data = []
                for res in results:
                    result_data.append((0, 0, {
                        'record_id': res.id,
                        'record_name': res.display_name,
                        'model': record.model_name,
                    }))
                record.result_ids = result_data
            except Exception as e:
                record.status = 'error'
                record.error_message = str(e)
                _logger.error(f"Error executing search: {e}")

    def _parse_natural_language(self):
        """Convert natural language to Odoo domain using LLM"""
        api_key = self.env['ir.config_parameter'].sudo().get_param('ovunque.openai_api_key')
        
        if not api_key:
            raise UserError(_(
                'OpenAI API key is not configured.\n\n'
                'To fix this:\n'
                '1. Go to Settings → Ovunque → API Settings\n'
                '2. Get your API key from openai.com/api/keys\n'
                '3. Paste the key (starts with "sk-")\n'
                '4. Save and try again\n\n'
                'Need help? Check the documentation in the module.'
            ))
        
        try:
            _logger.warning(f"[LLM] Starting query parsing for: {self.name}")
            _logger.warning(f"[LLM] Model name: {self.model_name}")
            
            if not self.model_name:
                raise UserError(_('No model selected. Please select a category.'))
            
            try:
                Model = self.env[self.model_name]
            except KeyError:
                raise UserError(_(
                    'The module for "%s" is not installed.\n\n'
                    'Please install the required module in Odoo:\n'
                    '1. Go to Apps\n'
                    '2. Search for "crm", "Sale", "Purchase", etc.\n'
                    '3. Click Install\n\n'
                    'Then come back and try again.'
                ) % self.model_name)
            
            model_fields = Model.fields_get()
            client = OpenAI(api_key=api_key)
            
            _logger.warning(f"[LLM] Model: {self.model_name}, Available fields: {len(model_fields)}")
            
            prompt = self._build_prompt(model_fields)
            _logger.warning(f"[LLM] Prompt length: {len(prompt)} chars")
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an Odoo domain filter generator. Convert natural language queries to Odoo domain syntax (Python list of tuples). Respond ONLY with valid Python list syntax. No explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            self.raw_response = response_text
            _logger.warning(f"[LLM] Response received: {response_text[:300]}")
            
            domain = self._parse_domain_response(response_text)
            return domain
            
        except UserError:
            raise
        except Exception as e:
            error_str = str(e).lower()
            _logger.error(f"[LLM ERROR] LLM parsing error: {str(e)}")
            
            if 'timeout' in error_str or 'connection' in error_str:
                raise UserError(_('Connection error with OpenAI. Please check your internet connection and try again.'))
            elif 'authentication' in error_str or 'invalid' in error_str or 'api' in error_str:
                raise UserError(_('OpenAI API key error. Please verify your API key in Settings → Ovunque → API Settings.'))
            elif 'rate' in error_str:
                raise UserError(_('You have exceeded OpenAI API rate limits. Please wait a few minutes and try again.'))
            else:
                raise UserError(_('Error communicating with OpenAI: %s\n\nPlease check Settings → Ovunque → API Settings.') % str(e)[:100])

    def _build_prompt(self, model_fields):
        """Build the prompt for LLM with available fields"""
        fields_info = self._get_field_info(model_fields)
        model_examples = self._get_model_examples()
        
        prompt = f"""TASK: Convert natural language query to Odoo domain (Python list of tuples).
RESPOND WITH ONLY THE DOMAIN LIST. NO EXPLANATIONS, NO MARKDOWN.

===== MODEL INFORMATION =====
Model: {self.model_name}
Description: {self._get_model_description()}

===== AVAILABLE FIELDS (DATABASE STORED ONLY - USE ONLY THESE) =====
{fields_info}

===== FIELD EXAMPLES FOR THIS MODEL =====
{model_examples}

===== RULES (CRITICAL - YOU MUST FOLLOW) =====
1. RESPOND WITH ONLY A PYTHON LIST: [(...), (...)]
2. EVERY field name must EXACTLY match one from the list above
3. Do NOT invent field names, do NOT use variations
4. Do NOT use computed fields (they are NOT in the list)
5. Operators: '=', '!=', '>', '<', '>=', '<=', 'ilike', 'like', 'in', 'not in'
6. Dates: YYYY-MM-DD format, e.g. '2025-01-15'
7. Numbers: plain integers/floats, NO currency symbols (100, not 100€)
8. Booleans: True/False (no quotes)
9. Many2one: use ('field.name', 'operator', 'text') OR ('field_id', '=', number)
10. SPECIAL: For product models, see the specific field mapping rules above (especially price fields)
11. IF you cannot safely create a domain → respond with: []

===== VALID RESPONSE EXAMPLES =====
[('state', '=', 'confirmed')]
[('name', 'ilike', 'test'), ('active', '=', True)]
[('date_start', '>=', '2025-01-01')]
[('price_total', '>', 1000)]
[]

===== YOUR TASK =====
Query: "{self.name}"
Response (ONLY the list, nothing else):"""
        return prompt

    def _get_field_info(self, model_fields):
        """Extract and format field information for LLM - ONLY stored fields"""
        fields_info = []
        for field_name, field_data in model_fields.items():
            if field_name.startswith('_'):
                continue
            
            is_stored = field_data.get('store', True) is not False
            if not is_stored:
                continue
            
            field_type = field_data.get('type', 'unknown')
            field_string = field_data.get('string', field_name)
            fields_info.append(f"- {field_name} ({field_type}): {field_string}")
        
        return "\n".join(fields_info[:50])
    
    def _get_model_description(self):
        """Get human-readable description of the model"""
        descriptions = {
            'res.partner': 'Contacts, Customers, Suppliers, Companies',
            'account.move': 'Invoices and Bills (posted documents)',
            'product.product': 'Product Variants (specific SKUs with combinations)',
            'product.template': 'Product Templates (prices, costs, inventory by template)',
            'sale.order': 'Sales Orders',
            'purchase.order': 'Purchase Orders',
            'stock.move': 'Stock Movements and Inventory',
            'crm.lead': 'CRM Leads and Opportunities',
            'project.task': 'Project Tasks and Work Items',
        }
        return descriptions.get(self.model_name, self.model_name)
    
    def _get_model_examples(self):
        """Get model-specific query examples"""
        examples = {
            'res.partner': """
- "Customers from Milan" → [('city', 'ilike', 'Milan'), ('customer_rank', '>', 0)]
- "Suppliers" → [('supplier_rank', '>', 0)]
- "Active contacts" → [('active', '=', True)]
- "Inactive partners" → [('active', '=', False)]""",
            'account.move': """
- "Unpaid invoices" → [('state', '!=', 'posted'), ('payment_state', '=', 'not_paid')]
- "Invoices from January 2025" → [('invoice_date', '>=', '2025-01-01'), ('invoice_date', '<', '2025-02-01')]
- "Large invoices over 1000" → [('amount_total', '>', 1000)]""",
            'product.product': """
- "Variants with barcode starting with 123" → [('barcode', 'like', '123')]
- "Active variants" → [('active', '=', True)]
- "Variants with default_code starting with SKU" → [('default_code', 'like', 'SKU')]
NOTE: For price/cost queries, use product.template model instead (prices are stored there)""",
            'product.template': """
IMPORTANT PRICE DISTINCTION:
- list_price = SELLING PRICE (what customer pays) - for queries about "price", "prezzo", "cost to customer"
- standard_price = INTERNAL COST (our cost) - only for "internal cost", "costo interno", "cost price"

EXAMPLES:
- "Products under 100 euros" → [('list_price', '<', 100)]
- "Articles cheaper than 50" → [('list_price', '<', 50)]
- "Products with selling price under 100" → [('list_price', '<', 100)]
- "Products with internal cost > 50" → [('standard_price', '>', 50)]
- "Products with our cost above 100" → [('standard_price', '>', 100)]
- "Active products" → [('active', '=', True)]
- "Low stock products" → [('qty_available', '<', 10), ('active', '=', True)]
- "Electronics products" → [('categ_id.name', 'ilike', 'Electronics')]

KEY RULE: If user mentions "price", "prezzo", "euro", "cost to customer" → ALWAYS use list_price
KEY RULE: If user specifically mentions "internal cost", "costo interno", "our cost", "cost price" → use standard_price""",
            'sale.order': """
- "Draft orders" → [('state', '=', 'draft')]
- "Confirmed sales from last month" → [('state', '=', 'sale')]
- "Orders over 500" → [('amount_total', '>', 500)]""",
            'purchase.order': """
- "RFQ pending" → [('state', '=', 'draft')]
- "Confirmed purchases" → [('state', 'in', ['purchase', 'done'])]""",
            'stock.move': """
- "In progress moves" → [('state', '=', 'confirmed')]
- "Done moves" → [('state', '=', 'done')]""",
            'crm.lead': """
- "Open opportunities" → [('probability', '>', 0), ('probability', '<', 100)]
- "Lost deals" → [('probability', '=', 0)]
- "Won deals" → [('probability', '=', 100)]""",
            'project.task': """
- "Open tasks" → [('state', 'in', ['todo', 'in_progress'])]
- "Completed tasks" → [('state', '=', 'done')]""",
        }
        return examples.get(self.model_name, "No specific examples available")

    def _parse_domain_response(self, response_text):
        """Parse the LLM response and validate it"""
        import re
        import ast
        try:
            cleaned = response_text.strip()
            _logger.warning(f"[PARSE] Original response (first 500 chars): {cleaned[:500]}")
            
            if cleaned.startswith('```'):
                cleaned = re.sub(r'^```python\n?', '', cleaned)
                cleaned = re.sub(r'^```\n?', '', cleaned)
                cleaned = re.sub(r'```.*$', '', cleaned, flags=re.DOTALL).strip()
                _logger.warning(f"[PARSE] After removing markdown: {cleaned[:500]}")
            
            match = re.search(r'\[.*\]', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(0)
                _logger.warning(f"[PARSE] Extracted list: {cleaned[:500]}")
            else:
                _logger.warning(f"[PARSE] No list found in response. Full response: {cleaned[:500]}")
            
            if not cleaned or cleaned == '[]':
                _logger.warning(f"[PARSE] Empty domain returned (query: {self.name})")
                return []
            
            try:
                domain = ast.literal_eval(cleaned)
            except (ValueError, SyntaxError) as e:
                _logger.warning(f"[PARSE] ast.literal_eval failed ({e}), attempting fallback repairs...")
                domain = self._attempt_domain_repair(cleaned)
            
            if not isinstance(domain, list):
                raise ValueError(f"Response is not a list: {type(domain)}")
            
            domain = self._fix_price_fields(domain)
            self._validate_domain_fields(domain)
            _logger.warning(f"[PARSE] Successfully parsed domain: {domain}")
            return domain
        except UserError:
            raise
        except Exception as e:
            _logger.error(f"[PARSE ERROR] Domain parsing failed: {str(e)}. Query: '{self.name}'. Raw response (first 300 chars): {response_text[:300]}")
            raise UserError(_(
                'The AI could not understand your search.\n\n'
                'Try:\n'
                '• Using simpler words\n'
                '• Being more specific (e.g., "invoices from January" instead of "old invoices")\n'
                '• Checking the category selection matches your query\n\n'
                'Error: %s'
            ) % str(e)[:80])
    
    def _validate_domain_fields(self, domain):
        """Validate that all fields in domain exist and are stored in the model"""
        if not domain:
            return
        
        Model = self.env[self.model_name]
        model_fields = Model.fields_get()
        
        for clause in domain:
            if not isinstance(clause, (tuple, list)) or len(clause) < 3:
                continue
            
            field_name = clause[0]
            
            if field_name in ('|', '&', '!'):
                continue
            
            base_field = field_name.split('.')[0]
            
            if base_field not in model_fields:
                stored_fields = self._get_available_stored_fields()
                error_msg = _(
                    'The field "%s" does not exist in this module.\n\n'
                    'AI may have misunderstood your query.\n\n'
                    'Available fields:\n%s\n\n'
                    'Try rephrasing your question or check the Debug Info tab for details.'
                ) % (base_field, stored_fields[:200])
                raise UserError(error_msg)
            
            field_data = model_fields[base_field]
            if field_data.get('store') is False:
                stored_fields = self._get_available_stored_fields()
                error_msg = _(
                    'The field "%s" is calculated, not stored in database.\n\n'
                    'This is a limitation of Odoo - use stored fields instead.\n\n'
                    'Try a different search or use one of these fields:\n%s'
                ) % (base_field, stored_fields[:200])
                raise UserError(error_msg)
            
            _logger.warning(f"[VALIDATE] Field '{base_field}' is valid and stored")
    
    def _fix_price_fields(self, domain):
        """Auto-fix LLM mistakes with price fields"""
        if not domain or self.model_name not in ('product.template', 'product.product'):
            return domain
        
        query_lower = self.name.lower()
        has_price_keywords = any(word in query_lower for word in ['prezzo', 'price', 'euro', '€', 'under', 'sopra', 'above', 'below', 'less', 'more', 'cheaper', 'expensive'])
        has_cost_keywords = any(word in query_lower for word in ['costo interno', 'internal cost', 'cost price', 'nostra cost', 'our cost'])
        
        for i, clause in enumerate(domain):
            if not isinstance(clause, (tuple, list)) or len(clause) < 3:
                continue
            
            field_name = clause[0]
            operator = clause[1]
            value = clause[2]
            
            if field_name == 'standard_price' and self.model_name == 'product.template':
                if has_price_keywords and not has_cost_keywords:
                    _logger.warning(f"[FIX] Query '{self.name}' on template uses standard_price, but looks like a selling price query. Changing to list_price")
                    domain[i] = ('list_price', operator, value)
            
            elif field_name == 'list_price' and self.model_name == 'product.product':
                error_msg = _(
                    'Price search not available for Product Variants.\n\n'
                    'Solution: Change the category to "Prodotti" (Products)\n'
                    'The system will automatically select the right model.\n\n'
                    'Technical info:\n'
                    '• Product Templates: have prices (list_price, standard_price)\n'
                    '• Product Variants: have SKU/barcode info only'
                )
                raise UserError(error_msg)
        
        return domain
    
    def _get_available_stored_fields(self):
        """Get comma-separated list of available stored fields"""
        Model = self.env[self.model_name]
        model_fields = Model.fields_get()
        
        stored = []
        for field_name, field_data in model_fields.items():
            if field_name.startswith('_'):
                continue
            if field_data.get('store') is not False:
                stored.append(field_name)
        
        return ', '.join(sorted(stored)[:20])
    
    def _attempt_domain_repair(self, domain_str):
        """Attempt to repair common LLM syntax errors"""
        import ast
        repairs = [
            (r"'\"", "'"),
            (r"\"'", "'"),
            (r"True", "True"),
            (r"False", "False"),
            (r"None", "None"),
        ]
        
        for pattern, replacement in repairs:
            domain_str = domain_str.replace(pattern, replacement)
        
        try:
            return ast.literal_eval(domain_str)
        except:
            try:
                return eval(domain_str)
            except:
                _logger.error(f"[REPAIR] Failed to repair domain: {domain_str[:200]}")
                return []


class SearchResult(models.Model):
    _name = 'search.result'
    _description = 'Search Query Result'
    _order = 'id desc'

    query_id = fields.Many2one('search.query', 'Query', ondelete='cascade', required=True)
    record_id = fields.Integer('Record ID', required=True)
    record_name = fields.Char('Record Name', required=True)
    model = fields.Char('Model', required=True)
