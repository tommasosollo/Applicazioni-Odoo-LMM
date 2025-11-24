import requests
import json
from odoo import models
from odoo.exceptions import UserError

class AIService(models.AbstractModel):
    _name = "ai.data.assistant.service"
    _description = "LLM Service for Data Assistant"

    def _call_llm(self, prompt):
        icp = self.env["ir.config_parameter"].sudo()
        api_key = icp.get_param("ai_data_assistant.api_key")
        if not api_key:
            raise ValueError("API key non configurata")
        
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=30)
            r.raise_for_status()
            print("LLM raw response:", r.text)
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                raise ValueError("LLM ha restituito risposta vuota")
            return content
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Errore nella chiamata all'LLM: {e}") from e

