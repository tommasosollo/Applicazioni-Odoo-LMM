from odoo import models, fields, api
from odoo.exceptions import UserError

class NLQueryWizard(models.TransientModel):
    _name = "ai.nl.query.wizard"
    _description = "Natural Language Query Wizard"

    user_query = fields.Text("Ask in Natural Language")
    model_id = fields.Many2one(
        "ir.model",
        string="Select Model",
        required=True,
        help="Choose the model to query"
    )

    def action_execute(self):
        if not self.model_id:
            raise UserError("Devi selezionare un modello.")

        engine = self.env["ai.nl.query.engine"]

        # Passiamo il nome del modello selezionato all'engine
        q = engine.nl_to_orm(self.user_query, model_name=self.model_id.model)
        model_name = q.get("model")
        domain = q.get("domain", [])
        limit = q.get("limit", 50)

        if model_name not in self.env.registry.models:
            raise UserError(f"Modello {model_name} inesistente.")

        # Proviamo a trovare una tree view attiva
        tree_view = self.env.ref("sale.view_order_tree", raise_if_not_found=False)

        if not tree_view:
            raise UserError("Il modello sale.order non ha alcuna tree view valida attiva.")

        # Restituiamo azione con tree view forzata
        return {
            "type": "ir.actions.act_window",
            "name": f"Query Results ({model_name})",
            "res_model": model_name,
            "view_mode": "tree",
            "view_id": tree_view.id,
            "domain": domain,
            "target": "current",
            "limit": limit,
        }

