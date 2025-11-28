import json
import logging
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class SearchController(http.Controller):
    
    @http.route('/ovunque/search', type='jsonrpc', auth='user', methods=['POST'])
    def natural_language_search(self, **kwargs):
        """API endpoint for natural language search"""
        try:
            query_text = kwargs.get('query')
            category = kwargs.get('category')
            model_name = kwargs.get('model')
            
            if not query_text:
                return {
                    'success': False,
                    'error': 'Missing query parameter'
                }
            
            if not category and not model_name:
                return {
                    'success': False,
                    'error': 'Missing category or model parameter'
                }
            
            SearchQuery = request.env['search.query']
            create_vals = {
                'name': query_text,
            }
            
            if category:
                create_vals['category'] = category
            elif model_name:
                create_vals['model_name'] = model_name
            
            search_record = SearchQuery.create(create_vals)
            
            search_record.action_execute_search()
            
            if search_record.status == 'success':
                Model = request.env[search_record.model_name]
                domain = eval(search_record.model_domain)
                results = Model.search(domain)
                
                results_data = []
                for record in results[:50]:
                    results_data.append({
                        'id': record.id,
                        'display_name': record.display_name,
                    })
                
                return {
                    'success': True,
                    'results': results_data,
                    'count': len(results),
                    'domain': search_record.model_domain,
                    'query_id': search_record.id,
                }
            else:
                return {
                    'success': False,
                    'error': search_record.error_message
                }
                
        except Exception as e:
            _logger.error(f"Search API error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/ovunque/models', type='jsonrpc', auth='user')
    def get_available_models(self, **kwargs):
        """Get list of available categories and models for search"""
        try:
            SearchQuery = request.env['search.query']
            categories = []
            models = []
            
            for category_code, category_label in SearchQuery._fields['category'].selection:
                categories.append({
                    'code': category_code,
                    'label': category_label,
                })
            
            for model_code, model_label in SearchQuery.AVAILABLE_MODELS:
                models.append({
                    'name': model_code,
                    'label': model_label,
                })
            
            return {
                'success': True,
                'categories': categories,
                'models': models
            }
        except Exception as e:
            _logger.error(f"Get models error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/ovunque/debug-fields', type='http', auth='user')
    def debug_model_fields(self, **kwargs):
        """Debug endpoint: List all stored fields for a model"""
        try:
            model_name = kwargs.get('model')
            
            if not model_name:
                return {
                    'success': False,
                    'error': 'Missing model parameter'
                }
            
            Model = request.env[model_name]
            model_fields = Model.fields_get()
            
            stored_fields = []
            computed_fields = []
            
            for field_name, field_data in sorted(model_fields.items()):
                if field_name.startswith('_'):
                    continue
                
                field_type = field_data.get('type', 'unknown')
                field_string = field_data.get('string', field_name)
                is_stored = field_data.get('store', True) is not False
                
                field_info = {
                    'name': field_name,
                    'type': field_type,
                    'label': field_string,
                }
                
                if is_stored:
                    stored_fields.append(field_info)
                else:
                    computed_fields.append(field_info)
            
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: monospace; margin: 20px; }}
                    .section {{ margin: 20px 0; padding: 10px; border: 1px solid #ccc; }}
                    .stored {{ background: #e8f5e9; }}
                    .computed {{ background: #fff3e0; }}
                    table {{ width: 100%; border-collapse: collapse; }}
                    td, th {{ padding: 8px; text-align: left; border: 1px solid #ddd; }}
                    th {{ background: #f0f0f0; font-weight: bold; }}
                </style>
            </head>
            <body>
                <h2>Model: {model_name}</h2>
                
                <div class="section stored">
                    <h3>Stored Fields ({len(stored_fields)}) - USE ONLY THESE IN QUERIES</h3>
                    <table>
                        <tr><th>Field Name</th><th>Type</th><th>Label</th></tr>
            """
            
            for field in stored_fields:
                html += f"<tr><td><code>{field['name']}</code></td><td>{field['type']}</td><td>{field['label']}</td></tr>"
            
            html += """
                    </table>
                </div>
                
                <div class="section computed">
                    <h3>Computed Fields ({}) - DO NOT USE</h3>
                    <table>
                        <tr><th>Field Name</th><th>Type</th></tr>
            """.format(len(computed_fields))
            
            for field in computed_fields[:50]:
                html += f"<tr><td><code>{field['name']}</code></td><td>{field['type']}</td></tr>"
            
            html += """
                    </table>
                </div>
            </body>
            </html>
            """
            
            return Response(html, mimetype='text/html')
        except Exception as e:
            _logger.error(f"Debug fields error: {e}")
            error_response = {
                'success': False,
                'error': str(e)
            }
            return Response(
                json.dumps(error_response),
                mimetype='application/json',
                status=400
            )
