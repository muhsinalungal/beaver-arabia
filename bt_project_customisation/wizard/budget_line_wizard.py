# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class BudgetLineWizard(models.TransientModel):
	_name = "budget.line.wizard"
	_rec_name = "analytic_account_id"
	
	general_budget_ids = fields.Many2many('account.budget.post', 'account_budget_post_rel', string='Budgetary Position')
	analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

	@api.model
	def default_get(self, fields):
		res = super().default_get(fields)
		ctx = self.env.context
		if ctx.get("active_model") == "budget.budget" and ctx.get("active_ids"):
			ids = ctx["active_ids"]
			crossovered_budget_obj = self.env['budget.budget'].browse(ids)
			
			res["analytic_account_id"] = crossovered_budget_obj.analytic_account_id.id
		return res
	
	def add_budget_lines(self):
		active_id = self.env.context.get('active_id')
		crossovered_budget_obj = self.env['budget.budget'].browse(active_id)
		general_budgets = self.general_budget_ids
		
		for budget in general_budgets:
			line_name = budget.name + ' - ' + self.analytic_account_id.name
			name_list = list(set(crossovered_budget_obj.budget_line_ids.mapped('value_y')))
			vals_list = list(set(crossovered_budget_obj.budget_line_ids.mapped('general_budget_id')))
			gen_budget_id = budget.id
			account_id = self.analytic_account_id.id
			if line_name not in name_list:
				crossovered_budget_obj._compute_xy_vals(line_name, gen_budget_id, account_id)

			action = {
				'name': _('Planning'),
				'view_mode': 'tree',
				'res_model': 'budget.lines',
				'view_id': self.env.ref('bt_project_customisation.budget_lines_tree').id,
				'type': 'ir.actions.act_window',
				'domain': [('budget_id', '=',crossovered_budget_obj.id )],
				'search_view_id': [self.env.ref('bt_project_customisation.view_budget_line_search').id, 'search'],
				'context': {'search_default_category_id_grp': 1,'search_default_month': 1}
			}
		
		
		return action

class CreateProjectWiz(models.TransientModel):
	_name = "create.project.wiz"
	
	
	name = fields.Char(string='Project Name')
	analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

	@api.model
	def default_get(self, fields):
		res = super(CreateProjectWiz, self).default_get(fields)
		res_id = self._context.get('active_id')

		order = self.env['sale.order'].browse(res_id)
	   
		res.update({
			'name': order.estimate_sheet_id.project_name,
			
		})
		return res
	
	
	def add_budget_lines(self):
		active_id = self.env.context.get('active_id')
		order_obj = self.env['sale.order'].browse(active_id)
		order_obj.action_create_project(self.name)
		
		return True
	
