# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning



class Project(models.Model):
	_inherit = "project.project"

	forcast_line_ids = fields.One2many('project.expense.forcast','project_id')
	estimate_sheet_id = fields.Many2one('estimate.sheet.summary', "Sale Estimate")

	def action_view_budget(self):
		action = self.env['ir.actions.act_window']._for_xml_id('base_account_budget.act_budget_view')
		action['domain'] = [('project_id', '=', self.id)]
		action['context'] = {'default_project_id': self.id, 'default_analytic_account_id': self.analytic_account_id.id,'default_name':self.name}
		return action

	def action_view_tasks(self):
		action = self.with_context(active_id=self.id, active_ids=self.ids) \
			.env.ref('project.open_view_project_all') \
			.sudo().read()[0]
		action['views'] = [(self.env.ref('project.edit_project').id, 'form')]
		action['res_id'] = self.id
		action['display_name'] = self.name
		return action

	def action_view_stock(self):
		action = self.env['ir.actions.act_window']._for_xml_id('bt_project_customisation.location_open_quants_project')
		action['domain'] = [('location_id', '=', self.site_location_id.id)]
		return action


	def action_move_closing_project(self):
		wip_acc = self.env['account.account'].search([('code', '=','1103102'),
													  ], limit=1)
		stock_acc = self.env['account.account'].search([('code', '=','1103101'),
													  ], limit=1)
		expense_acc = self.env['account.account'].search([('code', '=','5114101'),
													  ], limit=1)
		self._cr.execute('''
					SELECT sum(debit - credit)
					FROM account_move_line 
					WHERE account_id = %s AND
				
					move_id in (SELECT id FROM account_move WHERE state=%s)
				''',[stock_acc.id,'posted',])
		res = self._cr.fetchone()[0]
		
		if res != None:
			stock_sales_value = res
		else:
			stock_sales_value = 0.0

		self._cr.execute('''
					SELECT sum(debit - credit)
					FROM account_move_line 
					WHERE account_id = %s AND analytic_account_id = %s AND
				
					move_id in (SELECT id FROM account_move WHERE state=%s)
				''',[wip_acc.id,self.analytic_account_id.id,'posted',])
		res1 = self._cr.fetchone()[0]
		
		if res != None:
			wip_value = res1
		else:
			wip_value = 0.0

		current_stock_value = wip_value

		
		am = (
			self.env["account.move"]
			.with_context(
				force_company=self.company_id.id,
				company_id=self.company_id.id,
			)
			.create(
				{
					"journal_id": 17,
					"line_ids": [
			                    (0,0, {
									"name": "Closing of " + self.name,
									"partner_id": self.partner_id.id or False,
									"account_id": wip_acc.id,
									
									"credit": (
										current_stock_value or 0.0
									),
									"debit": (
									   0.0
									),
								   

								}),

			                    (0,0, {
									"name": "Closing of " + self.name,
									"partner_id": self.partner_id.id or False,
									"account_id": expense_acc.id,
									
									"credit": (
										 0.0
									),
									"debit": (
									 current_stock_value or 0.0
									),
								   

								}),
			                ],
					"company_id": self.company_id.id,
					"ref": self.name,
				   
				}
			)
		)
		# am.post()
		# self.analytic_account_id.active = False
		# self.active = False

		





class Task(models.Model):
	_name = "project.task"
	_inherit = "project.task"



	total_timesheet_cost = fields.Float("Timesheet Cost", compute='_compute_timesheet_cost',store=True,)
	# total_timesheet_cost_new1 = fields.Float("Timesheet Cost", compute='_compute_timesheet_cost',store=True,)


	@api.depends('timesheet_ids.amount')
	def _compute_timesheet_cost(self):
		for task in self:
			task.total_timesheet_cost = round(sum(task.timesheet_ids.mapped('amount')), 2)


	# @api.depends('timesheet_ids')
	# def _compute_timesheet_cost(self):
	# 	print ('self_______________________',self,)
	# 	amount_converted = 0.00
	# 	for task in self:
	# 		for timesheet in task.timesheet_ids:
	# 			cost = timesheet.employee_id.timesheet_cost or 0.0
	# 			amount = -timesheet.unit_amount * cost
	# 			print ('amount================,amount',amount,cost)
	# 			amount_converted += timesheet.employee_id.currency_id._convert(
	# 				amount, timesheet.account_id.currency_id, self.env.company, timesheet.date)
	# 			print ('amount_converted================,amount',amount_converted)
	# 		task.total_timesheet_cost = amount_converted

class AccountAnalyticLine(models.Model):
	_inherit = "account.analytic.line"



	@api.onchange('unit_amount','employee_id')
	def onchange_timesheet_cost(self):
		
		for timesheet in self:
			cost = timesheet.employee_id.timesheet_cost or 0.0
			amount = -timesheet.unit_amount * cost
			amount_converted = timesheet.employee_id.currency_id._convert(
				amount, timesheet.account_id.currency_id, self.env.company, timesheet.date)
			timesheet.amount = amount_converted



class ProjectExpenseForecast(models.Model):
	_name = "project.expense.forcast"
	_check_company_auto = True
	
	name = fields.Char('Name',)

	description = fields.Char('Description',)
	product_id = fields.Many2one(
		'product.product',
		string='Product',

	)

	projected_amt = fields.Float(
		'Projected',
		
	)
	actual_amt = fields.Float(string='Actual',)

	project_id = fields.Many2one(
		'project.project',
		string='Project',
	)
	
	forcast_type = fields.Selection([
		('wages', 'Manpower'),
		('equipments', 'Equipments'),
		('material', 'Materials'),
		('tools', 'Consumable and Tools'),
		('accomodation', 'Accomodation'),
		('spare', 'Spare part / Machinery Import'),
		('inspection', 'Third Party Inspection'),
		('tech_visit', 'Technician Visit'),
		('vehicle', 'Hire Vehicle'),
		('transport', 'Transport - Trailer Hire'),
		('Repair', 'Repair & Maintenance'),
		('travel', 'Travel Expense'),
		('Consultancy', 'Consultancy Services'),
		('safety', 'Safety Items / PPE Expenses'),
		('misc', 'Miscellaneous Expense'),
		
	   ],
		
		track_visibility='onchange',
		copy='True',
	)


	@api.onchange('product_id')
	def _onchange_user_type_id(self):
	   
		if self.product_id:
			self.description = self.product_id.name
		else:
			self.description = ''
	   