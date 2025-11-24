from odoo import models
from odoo.exceptions import UserError
import json
import logging
import re

class NLQueryEngine(models.AbstractModel):
    _name = "ai.nl.query.engine"
    _inherit = "ai.data.assistant.service"
    _description = "Natural Language Query Engine"

    def nl_to_orm(self, query):
        prompt = f"""
Converti questa richiesta in una istruzione ORM Odoo 19.
Risposta SOLO in JSON:
- domain deve essere una lista valida per self.env['model'].search(domain)
- operatori logici "|", "&" devono essere in testa alle liste come in Odoo
- usare solo tuple/liste, valori hashable
{{
 "model": "...",
 "domain": [...],
 "fields": ["..."],S
 "limit": 100
}}

Testo: "{query}"
"""
        response = self._call_llm(prompt)

        response_clean = re.sub(r"^```json\s*|\s*```$", "", response.strip(), flags=re.DOTALL)

        # Sostituisci tuple con liste (solo parentesi tonde) in modo semplice
        response_clean = response_clean.replace("(", "[").replace(")", "]")

        try:
            return json.loads(response_clean)
        except json.JSONDecodeError:
            _logger = logging.getLogger(__name__)
            _logger.error("LLM response non JSON: %s", response)
            raise UserError("La risposta dell'LLM non è un JSON valido")

