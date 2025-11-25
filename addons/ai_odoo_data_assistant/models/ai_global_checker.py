from odoo import models, api, fields
import json

class AIGlobalChecker(models.AbstractModel):
    _name = "ai.global.checker"
    _description = "AI Global Duplicate Checker"

    ai_duplicate_data = fields.Text("AI Duplicate Data", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AIGlobalChecker, self).create(vals_list)
        for record, values in zip(records, vals_list):
            record._trigger_ai_cleaner(values)
        return records

    def write(self, vals):
        res = super(AIGlobalChecker, self).write(vals)
        for record in self:
            record._trigger_ai_cleaner(vals)
        return res

    def _trigger_ai_cleaner(self, values):      
        allowed_models = [
            "res.partner",
            "product.product",
            "sale.order",
            "purchase.order",
            "account.move",
        ]
        if self._name not in allowed_models:
            return

        cleaner = self.env["ai.data.cleaner"]
        response = cleaner.analyze_record(self._name, values)
        try:
            json.loads(response)
            self.ai_duplicate_data = response
        except Exception:
            self.ai_duplicate_data = "{}"