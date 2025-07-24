from odoo import models, fields, api, _



class AccountAnalyticInherit(models.Model):
    _inherit = "account.analytic.account"
    
    
    def name_get(self):
        res = []
        for analytic in self:
            code = analytic.code
            name = analytic.name
            if analytic.name:
                name = name
            if analytic.partner_id.commercial_partner_id.name:
                name = name
            res.append((analytic.id, name))
        return res

class CostCenter(models.Model):
    _inherit = "cost.center"


class AccountBudgetPost(models.Model):
    _inherit = "account.budget.post"

class AccountBudgetPostType(models.Model):
    _inherit = "account.budget.post.type"
