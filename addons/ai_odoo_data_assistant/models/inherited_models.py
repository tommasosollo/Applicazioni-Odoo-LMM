from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"
    ai_duplicate_data = fields.Text("AI Duplicate Data", readonly=True)

class ProductProduct(models.Model):
    _inherit = "product.product"
    ai_duplicate_data = fields.Text("AI Duplicate Data", readonly=True)

class SaleOrder(models.Model):
    _inherit = "sale.order"
    ai_duplicate_data = fields.Text("AI Duplicate Data", readonly=True)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    ai_duplicate_data = fields.Text("AI Duplicate Data", readonly=True)

class AccountMove(models.Model):
    _inherit = "account.move"
    ai_duplicate_data = fields.Text("AI Duplicate Data", readonly=True)