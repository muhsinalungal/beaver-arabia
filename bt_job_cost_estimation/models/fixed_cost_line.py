# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta


class Estimateline(models.Model):
    _name = "fixed.cost.line"

    sale_template_id = fields.Many2one('sale.template')
    name = fields.Char('Description')
    cost = fields.Float('Cost', )
    sequence = fields.Integer('Sequence')
