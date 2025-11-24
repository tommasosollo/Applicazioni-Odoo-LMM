from odoo import models, fields
from odoo.exceptions import UserError
import json
import re

class NLQueryEngine(models.AbstractModel):
    _name = "ai.nl.query.engine"
    _inherit = "ai.data.assistant.service"
    _description = "Natural Language Query Engine"

    def nl_to_orm(self, query, model_name=None):

        if not model_name:
            raise UserError("Devi specificare il modello per la query.")


        prompt = f"""
Sei un convertitore da linguaggio naturale a query Odoo ORM.
L'utente ha scelto il modello: {model_name}

### REGOLE IMPORTANTI
1. Puoi usare SOLO i campi del modello selezionato.
2. NON inventare campi.
3. La risposta deve essere JSON valido con questa struttura:
{{
  "model": "{model_name}",
  "domain": [ ... ],
  "fields": ["campo1", "campo2", ...],
  "limit": 50
}}

### Query utente:
{query}

Rispondi SOLO con JSON valido senza alcun testo extra.
"""
        def extract_json_from_llm(response_raw):
            """
            Estrae la prima stringa JSON valida dall'output LLM.
            """

            def flatten(obj):
                if isinstance(obj, list):
                    for item in obj:
                        res = flatten(item)
                        if res:
                            return res
                elif isinstance(obj, dict):
                    if "content" in obj:
                        return flatten(obj["content"])
                    else:
                        for v in obj.values():
                            res = flatten(v)
                            if res:
                                return res
                elif isinstance(obj, str):
                    s = obj.strip()
                    # Prova a fare parse JSON direttamente
                    try:
                        json.loads(s)
                        return s
                    except:
                        # rimuovi blocchi markdown ```json ... ```
                        s_clean = re.sub(r"^```json\s*|\s*```$", "", s, flags=re.DOTALL).strip()
                        try:
                            json.loads(s_clean)
                            return s_clean
                        except:
                            return None
                return None

            json_str = flatten(response_raw)
            if not json_str:
                raise UserError(f"LLM non ha restituito JSON valido. Raw response: {response_raw}")
            return json.loads(json_str)

        response_raw = self._call_llm(prompt)
        print("Raw LLM response:", response_raw)
        q = extract_json_from_llm(response_raw)


        return q
