# -*- encoding: UTF-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015-Today Laxicon Solution.
#    (<http://laxicon.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

# import models
from odoo import api, models
class accountdeit(models.Model):
    _inherit = "account.move"

    def total_debit_credit(self):
        res = {}
        for move in self:
            dr_total = 0.00
            cr_total = 0.00
            for line in move.line_ids:
                dr_total += line.debit
                cr_total += line.credit
            res.update({'cr_total': round(cr_total,2), 'dr_total': round(dr_total,2)})
        return res
