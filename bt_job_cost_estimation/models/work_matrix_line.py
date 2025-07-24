from odoo import models,fields

class SaleOrder(models.Model):
    _name = "work.matrix.line"

    name = fields.Char("Activities And Responsibilities")
    contractor = fields.Char("Contractor")
    gambit = fields.Char("Gambit")
    sequence = fields.Integer("Sequence")
    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
