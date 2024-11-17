# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        #inherit of the function from account.move to update asset value from vendor bills

        res = super(AccountMove, self).action_post()
        line_ids = self.mapped('invoice_line_ids').filtered(lambda line: line.asset_id)
        for line in line_ids:
            try:
                line.asset_id.purchase_value = line.price_unit
            except UserError:
                # a UserError here means the SO was locked, which prevents changing the taxes
                # just ignore the error - this is a nice to have feature and should not be blocking
                pass
        return res
