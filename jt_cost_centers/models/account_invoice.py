# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    cost_center_id = fields.Many2one("cost.center", string='Cost Center')

    @api.model
    def default_get(self, fields):
        result = super(AccountInvoice, self).default_get(fields)
        if result.get('purchase_id'):
            po_id = result.get('purchase_id')
            purchase_order = self.env['purchase.order'].browse(po_id)
            result.update(
                {'cost_center_id': purchase_order.cost_center_id and purchase_order.cost_center_id.id or False})
        return result

    @api.onchange('cost_center_id')
    def set_cost_center(self):
        for line in self.invoice_line_ids:
            line.cost_center_id = self.cost_center_id.id


class AccountInvoiceLine(models.Model):

    _inherit = 'account.move.line'

    cost_center_id = fields.Many2one("cost.center", string="Cost Center",)

    purchase_line_id = fields.Many2one(
        'purchase.order.line', 'Purchase Order Line', ondelete='set null', index=True)

    @api.onchange('quantity')
    def set_default_cost_center(self):
        if self.move_id.cost_center_id:
            self.cost_center_id = self.move_id.cost_center_id.id

    # @api.model
    # def create(self, vals):

    #     if vals.get('move_id'):
    #         if self.env['account.move'].browse(vals.get('move_id')).cost_center_id:
    #             vals['cost_center_id'] = self.env['account.move'].browse(vals.get('move_id')).cost_center_id.id
            
    #     return super(AccountInvoiceLine, self).create(vals)
