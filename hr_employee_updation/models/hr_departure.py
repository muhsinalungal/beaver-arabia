# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrDepartureWizard(models.TransientModel):
	_inherit = 'hr.departure.wizard'
	_description = 'Departure Wizard'

	

	def action_register_departure(self):
		super(HrDepartureWizard, self).action_register_departure()
		employee = self.employee_id
		employee.active = True
		employee.archive = True