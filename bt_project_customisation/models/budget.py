#BroadTech IT Solutions Pvt Ltd.
#bbbn

from odoo import api, fields, models, _
from collections import namedtuple
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class BudgetBudget(models.Model):
	_inherit = 'budget.budget'
	
	project_id = fields.Many2one('project.project', 'Project')
	general_budget_id = fields.Many2one('account.budget.post', 'Select Budgetary Position')
	analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
	budget_line_ids = fields.One2many('crossovered.budget.matrix', 'crossovered_budget_id', 'Budget Lines')
	


	@api.onchange('project_id')
	def onchange_project_id(self):
		for budget in self:
			if budget.project_id and budget.project_id.analytic_account_id:
				budget.analytic_account_id=budget.project_id.analytic_account_id.id

	def action_view_budget_lines(self):
		action = self.env['ir.actions.act_window']._for_xml_id('bt_project_customisation.budget_lines_action')
		action['domain'] = [('budget_id', '=', self.id)]
		return action



	@api.depends('date_from', 'date_to')
	def _compute_xy_vals(self, line_name, gen_budget_id, account_id):
		matrix_vals = []
		budget = self or False
		if not budget or not (budget.date_from and budget.date_to):
			return
		line_name = line_name or ''
		gen_budget_id = gen_budget_id or False
		account_id = account_id or False
		start_date = budget.date_from
		end_date = budget.date_to
		budget_line_obj = self.env['budget.lines']
		one_day = timedelta(1)
		start_dates = [start_date]
		end_dates = []
		today = start_date
		while today <= end_date:
			tomorrow = today + one_day
			if tomorrow.month != today.month:# and tomorrow.month <= end_date.month:
				start_dates.append(tomorrow)
				end_dates.append(today)
			today = tomorrow
		
		end_dates.append(end_date)
		out_fmt = '%d/%m/%Y'
		i = 1
		for start, end in zip(start_dates,end_dates):
			if start > end_date:
				break
			i += 1
			x_name = '{} to {}'.format(start.strftime(out_fmt), end.strftime(out_fmt))
			x_name_planned = x_name
			x_name_actual = x_name + ' ' + 'Actual' 
			matrix = (0,0,{
				'value_x':x_name_planned,
				'value_head':'Material',
				'value_y':line_name,
				'crossovered_budget_id':budget.id,
				'general_budget_id':gen_budget_id,
				'analytic_account_id':account_id,
				'date_from':start,
				'date_to':end,
				})
			matrix_vals.append(matrix)
		budget.budget_line_ids = matrix_vals
		
	def _prepare_budget_line_vals(self, record):
		return {
				'general_budget_id':record.general_budget_id.id if record.general_budget_id else False,
				'category_id':record.general_budget_id.category_id.id if record.general_budget_id.category_id else False,
				'analytic_account_id':record.analytic_account_id.id if record.analytic_account_id else False,
				'budget_id':self.id,
				'date_from':record.date_from,
				'date_to':record.date_to,
				'planned_amount':record.planned_amount,
				'matrix_line_id':record.id,
				
			}
	
	def button_add_budget(self):
		if self.general_budget_id and self.analytic_account_id:
			line_name = self.general_budget_id.name + ' - ' + self.analytic_account_id.name
			name_list = list(set(self.budget_line_ids.mapped('value_y')))
			vals_list = list(set(self.budget_line_ids.mapped('general_budget_id')))
			gen_budget_id = self.general_budget_id.id
			account_id = self.analytic_account_id.id
			if line_name not in name_list:
				self._compute_xy_vals(line_name, gen_budget_id, account_id)
			self.general_budget_id = False
		elif self.general_budget_id and not self.analytic_account_id:
			raise UserError(_('Analytic Account is not given!'))
			
	@api.onchange('general_budget_id')
	def onchange_general_budget_id(self):
		for budget in self:
			if not budget.analytic_account_id and budget.general_budget_id:
				raise UserError(_('Analytic Account is not given!'))
	
	# def action_budget_confirm(self):
	# 	result = super(BudgetBudget, self).action_budget_confirm()
	# 	for rec in self:
	# 		if rec.state == 'confirm' and rec.budget_line_ids:
	# 			rec.budget_line_ids.unlink()
	# 	return result

	
class CrossoveredBudgetMatrix(models.Model):
	_name = 'crossovered.budget.matrix'
	
	name = fields.Char(string='Name',)
	value_x = fields.Char(string='Date Name',)
	value_xx = fields.Char(string='Date Name',)
	value_y = fields.Char(string='Project Name',)
	value_head = fields.Char(string='Header',)
	crossovered_budget_id = fields.Many2one('budget.budget', 'Budget ID')
	planned_amount = fields.Float('Planned Amount')
	qty = fields.Float('Qty')
	general_budget_id = fields.Many2one('account.budget.post', 'Budgetary Position')
	analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
	date_from = fields.Date(string='Date From', readonly=True)
	date_to = fields.Date(string="Date To", readonly=True)
	
	def _create_update_budget_lines_from_matrix(self):
		self.ensure_one()
		budget_matrix_ids = []
		budget_line_obj = self.env['budget.lines']
		budget_matrix_obj = self.env['crossovered.budget.matrix']
		crossover_budget_id = self.crossovered_budget_id.id if self.crossovered_budget_id else False
		if not crossover_budget_id:
			return
		budget_line_rec = budget_line_obj.search([('matrix_line_id','=',self.id), ('budget_id','=',crossover_budget_id)])
		if self.crossovered_budget_id.state == 'draft' and not budget_line_rec:
			line_vals = self.crossovered_budget_id._prepare_budget_line_vals(self)
			budget_line_obj.create(line_vals)
		else:
			if budget_line_rec.planned_amount != self.planned_amount:
				budget_line_rec.write({
					'planned_amount':self.planned_amount,
					})
	
	@api.model
	def create(self, vals):
		result = super(CrossoveredBudgetMatrix, self).create(vals)
		if result:
			crossover_budget = result.crossovered_budget_id
			if crossover_budget:
				result._create_update_budget_lines_from_matrix()
		return result
	
	def write(self, vals):
		result = super(CrossoveredBudgetMatrix, self).write(vals)
		budget_line_obj = self.env['budget.lines']
		for rec in [r for r in self if r.crossovered_budget_id and r.crossovered_budget_id.state == 'draft']:
			crossover_budget_id = rec.crossovered_budget_id.id if rec.crossovered_budget_id else False
			budget_line_rec = budget_line_obj.search([('matrix_line_id','=',rec.id), ('budget_id','=',crossover_budget_id)])
			if not budget_line_rec:
				line_vals = self.crossovered_budget_id._prepare_budget_line_vals(rec)
				budget_line_obj.create(line_vals)
			else:
				if budget_line_rec.planned_amount != rec.planned_amount:
					budget_line_rec.write({
						'planned_amount':rec.planned_amount,
						})
		return result
		
		
class BudgetLines(models.Model):
	_inherit = 'budget.lines'
	
	matrix_line_id = fields.Many2one('crossovered.budget.matrix', 'Matrix ID')
	category_id = fields.Many2one('account.budget.post.type', string='Category')
	qty = fields.Float( string='Quantity')
	unit_price = fields.Float( string='Unit Price')
	estimated_cost = fields.Float( string='Estimated Cost',compute='_compute_estimated_amount',)


	@api.onchange('general_budget_id')
	def onchange_general_budget_id(self):
		for budget in self:
			if budget.general_budget_id.product_id:
				budget.unit_price = budget.general_budget_id.product_id.lst_price
			else:
				budget.unit_price = 0.00

	@api.onchange('general_budget_id','qty')
	def onchange_unit_amt(self):
		for budget in self:
			
			budget.unit_price = budget.general_budget_id.product_id.lst_price if budget.general_budget_id.product_id else 0.00
		

	@api.onchange('general_budget_id','qty','unit_price')
	def onchange_planned_amt(self):
		for budget in self:
			
			budget.planned_amount = budget.qty * budget.unit_price

	def _compute_estimated_amount(self):
		for line in self:
			result = 0.0
			estimate_lines = self.env['sale.estimate.line'].search([('sheet_id', '=', line.budget_id.project_id.estimate_sheet_id.id),
                                                                      ('general_budget_id','=', line.general_budget_id.id),
                                                                      ])
			if estimate_lines:
				line.estimated_cost = estimate_lines.subtotal
			else:
				line.estimated_cost = 0.00
			

	def _compute_practical_amount(self):
		for line in self:
			result = 0.0
			acc_ids = line.general_budget_id.account_ids.ids
			# product_id = line.general_budget_id.product_id.id
			# if product_id:
			# 	product_id = product_id
			# else:
			# 	product_id = 1
			date_to = self.env.context.get('wizard_date_to') or line.date_to
			date_from = self.env.context.get('wizard_date_from') or line.date_from
			if line.general_budget_id.timesheet == True:
				if line.analytic_account_id.id:
					self.env.cr.execute("""
						SELECT SUM(amount)
						FROM account_analytic_line
						WHERE account_id=%s
							AND date between %s AND %s AND sheet_id IS NOT NULL
							""",
										(line.analytic_account_id.id, date_from, date_to,))
					result = self.env.cr.fetchone()[0] or 0.0
			else:
				if line.analytic_account_id.id:
					result = 0.00
					product_id = line.general_budget_id.product_id.id
					if product_id:
						self.env.cr.execute("""
							SELECT SUM(amount)
							FROM account_analytic_line
							WHERE account_id=%s
								AND date between %s AND %s
								AND general_account_id=ANY(%s) AND product_id=%s""",
											(line.analytic_account_id.id, date_from, date_to, acc_ids,product_id,))
						result = self.env.cr.fetchone()[0] or 0.0
					self.env.cr.execute("""
						SELECT SUM(amount)
						FROM account_analytic_line
						WHERE account_id=%s
							AND date between %s AND %s
							AND general_account_id=ANY(%s) AND budgetry_position_id=%s""",
										(line.analytic_account_id.id, date_from, date_to, acc_ids,line.general_budget_id.id,))
					result2 = self.env.cr.fetchone()[0] or 0.0
					# self.env.cr.execute("""
					# 	SELECT SUM(total)
					# 	FROM stock_move_line
					# 	WHERE move_id in (SELECT id FROM stock_move WHERE analytic_account_id = %s)
					# 	    AND state=%s
					# 		AND date between %s AND %s
					# 		 AND product_id=%s""",
					# 					(line.analytic_account_id.id,'done', date_from, date_to,product_id,))
					# stock_result = self.env.cr.fetchone()[0] or 0.0
			line.practical_amount = result + result2
	
	def _create_update_matrix_line_from_budget_line(self):
		self.ensure_one()
		matrix_obj = self.env['crossovered.budget.matrix']
		crossover_budget_id = self.budget_id.id
		matrix_line_rec = matrix_obj.search([('id','=',self.matrix_line_id.id)]) if self.matrix_line_id else False
		if not matrix_line_rec:
			# pass
			line_vals = self._prepare_matrix_line_vals()
			new_matrix_line = matrix_obj.create(line_vals)
			self.matrix_line_id = new_matrix_line.id
		else:
			line_vals = self._prepare_matrix_line_vals()
			matrix_line_rec.write(line_vals)
#     
	def _prepare_matrix_line_vals(self):
		self.ensure_one()
		value_y = self.general_budget_id.name + ' - ' + self.analytic_account_id.name
		out_fmt = '%m/%d/%Y'
		value_x = '{} to {}'.format(self.date_from.strftime(out_fmt), self.date_to.strftime(out_fmt)) 
		return {
			'general_budget_id':self.general_budget_id.id if self.general_budget_id else False,
			'analytic_account_id':self.analytic_account_id.id if self.analytic_account_id else False,
			'date_from':self.date_from,
			'date_to':self.date_to,
			'planned_amount':self.planned_amount,
			'value_y':value_y,
			'value_x':value_x,
		}
#     
	def write(self, vals):
		result = super(BudgetLines, self).write(vals)
		for rec in [r for r in self if r.budget_id and r.budget_id.state == 'draft']:
			matrix_line_vals = []
			budget_id = vals.get('general_budget_id',False)
			account_id = vals.get('analytic_account_id',False)
			date_from = vals.get('date_from',False)
			date_to = vals.get('date_to',False)
			planned_amount = vals.get('planned_amount',False)
			if (budget_id or account_id or date_from or date_to or planned_amount):
				rec._create_update_matrix_line_from_budget_line()
		return result
#     
#     @api.model
#     def create(self, vals):
#         print("_______________________________________")
#         
#         budget_id = vals.get('general_budget_id',False)
#         account_id = vals.get('analytic_account_id',False)
#         crossovered_budget_id = vals.get('crossovered_budget_id',False)
#         record_exists = self.env['crossovered.budget.lines'].search([('analytic_account_id','=',account_id),('general_budget_id','=',budget_id),('crossovered_budget_id','=',crossovered_budget_id)])
#         print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2          ",record_exists)
#         if record_exists:
#             print("++++++++++++++++++++++++++++++++++++++++++")
#             return False
#         result = super(CrossoveredBudgetLines, self).create(vals)
#         if result:
#             print("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK")
#             matrix_line_id = result.matrix_line_id
#             budget = result.crossovered_budget_id
#             if budget and budget.state == 'draft' and not matrix_line_id:
#                 print("OOOOOOOOOOOOPPPPPPPPPPPPPPP")
#                 result._create_update_matrix_line_from_budget_line()
#         return result
		
#     @api.multi
#     def unlink(self):

class AccountBudgetPost(models.Model):
	_inherit = 'account.budget.post'
	_order = "id asc"
	
	product_id = fields.Many2one('product.product', string='Product')
	timesheet = fields.Boolean(string='Is Timesheet')
	category_id = fields.Many2one('account.budget.post.type', string='Category')

class AccountBudgetPostTypes(models.Model):
	_name = 'account.budget.post.type'
	
	name = fields.Char(string='Name')
	code = fields.Char(string='Code')


