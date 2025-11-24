# models/res_config_settings.py
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_ai_duplicate_checker = fields.Boolean("Enable AI Duplicate Checker")
    module_ai_nl_query = fields.Boolean("Enable AI NL Query")
