# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# Copyright 2018-2019 Brainbean Apps (https://brainbeanapps.com)
# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import babel.dates
import logging
import re
from collections import namedtuple
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import MONTHLY, WEEKLY

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

empty_name = '/'

class hr_timesheet_type(models.Model):
	_name = 'hr.timesheet.type'
	_description = 'Timesheet Type'
	
	name = fields.Char(string='Type Name', required=True)
	max_hrs = fields.Float(string='Maximum Man hours Per Day')
	percentage = fields.Float(string='Percentage')
	account_id = fields.Many2one('account.account', string='Account')

class timesheet_project_manager_check(models.Model):
	_name = 'timesheet.project.manager.check'
	_description = 'timesheet_project_manager_check'
	
#     project_id = fields.Many2one(
#         comodel_name='project.project',
#         string='Project',
#     )
	is_validated = fields.Boolean(
		string='Validated',
		default=False,
#         compute='_check_and_validate'
	)
	user_id = fields.Many2one(
		comodel_name='res.users',
		string='Manager',
	)
	sheet_id = fields.Many2one(
		comodel_name='hr_timesheet.sheet',
	)
	
#     @api.multi
#     @api.depends('user_id', 'is_validated')
#     def _check_and_validate(self):
#         for line in self:
#             if line.user_id.id == self.env.user.id:
#                 print("--------------hello ____u got achance to edit this rec")
#             else:
#                 print("------------------not won the chance to edit this rec")
# #         self.env.user.id
#         return True

class AccountAnalyticLine(models.Model):
	_inherit = 'account.analytic.line'

	timesheet_type_id = fields.Many2one(
		comodel_name='hr.timesheet.type',
	)

	

class Sheet(models.Model):
	_inherit = 'hr_timesheet.sheet'
	_description = 'Timesheet Sheet'
   

   
	
	
	
	add_line_timesheet_type_id = fields.Many2one(
		comodel_name='hr.timesheet.type',
		string='Select Type',
		help='If selected, the associated type is added '
			 'to the timesheet sheet when clicked the button.',
	)
	
	

#     @api.multi
#     @api.depends('date_start', 'date_end')
#     def _compute_name(self):
#         locale = self.env.context.get('lang') or self.env.user.lang or 'en_US'
#         for sheet in self:
#             if sheet.date_start == sheet.date_end:
#                 sheet.name = babel.dates.format_skeleton(
#                     skeleton='MMMEd',
#                     datetime=datetime.combine(sheet.date_start, time.min),
#                     locale=locale,
#                 )
#                 continue

#             period_start = sheet.date_start.strftime(
#                 '%V, %Y'
#             )
#             period_end = sheet.date_end.strftime(
#                 '%V, %Y'
#             )

#             if period_start == period_end:
#                 sheet.name = '%s %s' % (
#                     _('Week'),
#                     period_start,
#                 )
#             else:
#                 sheet.name = '%s %s - %s' % (
#                     _('Weeks'),
#                     period_start,
#                     period_end,
#                 )

#     @api.depends('timesheet_ids.unit_amount')
#     def _compute_total_time(self):
#         for sheet in self:
#             sheet.total_time = sum(sheet.mapped('timesheet_ids.unit_amount'))

#     @api.multi
#     def _is_project_manager(self):
#         if self.employee_id.project_manager_id.user_id == self.env.user:
#             self.is_project_manager=True
#         else:
#             self.is_project_manager=False    
			
		
#     @api.multi
#     def _is_hr_manager(self):
#         if self.employee_id.parent_id.user_id == self.env.user:
#             self.is_hr_manager=True
#         else:
#             self.is_hr_manager=False
		
	
#     @api.multi        
#     def _is_approve_button_visible(self):
#         self.approve_button_visible = False
# #         for check_id in self.project_manager_check_ids:
# #             if check_id.user_id == self.env.user and not check_id.is_validated:
# #                 self.approve_button_visible = True
#         false_lines = self.env['timesheet.project.manager.check'].search([('sheet_id', '=', self.id), ('is_validated', '=', False), ('user_id', '=', self.env.user.id)])
#         if len(false_lines) != 0:
#             self.approve_button_visible = True
		
			
	
	
#     @api.multi
#     @api.depends('review_policy')
#     def _compute_possible_reviewer_ids(self):
#         for sheet in self:
#             sheet.possible_reviewer_ids = sheet._get_possible_reviewers()

#     @api.multi
#     @api.depends('possible_reviewer_ids')
#     def _compute_can_review(self):
#         for sheet in self:
#             sheet.can_review = self.env.user in sheet.possible_reviewer_ids

#     @api.model
#     def _search_can_review(self, operator, value):
#         if (operator == '=' and value) \
#                 or (operator in ['<>', '!='] and not value):
#             operator = '='
#         else:
#             operator = '!='
#         return [('possible_reviewer_ids', operator, self.env.uid)]

#     @api.depends('name', 'employee_id')
#     def _compute_complete_name(self):
#         for sheet in self:
#             complete_name = sheet.name
#             complete_name_components = sheet._get_complete_name_components()
#             if complete_name_components:
#                 complete_name = '%s (%s)' % (
#                     complete_name,
#                     ', '.join(complete_name_components)
#                 )
#             sheet.complete_name = complete_name

#     @api.constrains('date_start', 'date_end')
#     def _check_start_end_dates(self):
#         for sheet in self:
#             if sheet.date_start > sheet.date_end:
#                 raise ValidationError(
#                     _('The start date cannot be later than the end date.'))

#     @api.multi
#     def _get_complete_name_components(self):
#         """ Hook for extensions """
#         self.ensure_one()
#         return [self.employee_id.name_get()[0][1]]

#     @api.multi
#     def _get_overlapping_sheet_domain(self):
#         """ Hook for extensions """
#         self.ensure_one()
#         return [
#             ('id', '!=', self.id),
#             ('date_start', '<=', self.date_end),
#             ('date_end', '>=', self.date_start),
#             ('employee_id', '=', self.employee_id.id),
#             ('company_id', '=', self._get_timesheet_sheet_company().id),
#         ]

# #     @api.constrains(
# #         'date_start',
# #         'date_end',
# #         'company_id',
# #         'employee_id',
# #         'review_policy',
# #     )
# #     def _check_overlapping_sheets(self):
# #         for sheet in self:
# #             overlapping_sheets = self.search(
# #                 sheet._get_overlapping_sheet_domain()
# #             )
# #             if overlapping_sheets:
# #                 raise ValidationError(_(
# #                     'You cannot have 2 or more sheets that overlap!\n'
# #                     'Please use the menu "Timesheet Sheet" '
# #                     'to avoid this problem.\nConflicting sheets:\n - %s' % (
# #                         '\n - '.join(overlapping_sheets.mapped('complete_name')),
# #                     )
# #                 ))

#     @api.multi
#     @api.constrains('company_id', 'employee_id')
#     def _check_company_id_employee_id(self):
#         for rec in self.sudo():
#             if rec.company_id and rec.employee_id.company_id and \
#                     rec.company_id != rec.employee_id.company_id:
#                 raise ValidationError(
#                     _('The Company in the Timesheet Sheet and in '
#                       'the Employee must be the same.'))

#     @api.multi
#     @api.constrains('company_id', 'department_id')
#     def _check_company_id_department_id(self):
#         for rec in self.sudo():
#             if rec.company_id and rec.department_id.company_id and \
#                     rec.company_id != rec.department_id.company_id:
#                 raise ValidationError(
#                     _('The Company in the Timesheet Sheet and in '
#                       'the Department must be the same.'))

#     @api.multi
#     @api.constrains('company_id', 'add_line_project_id')
#     def _check_company_id_add_line_project_id(self):
#         for rec in self.sudo():
#             if rec.company_id and rec.add_line_project_id.company_id and \
#                     rec.company_id != rec.add_line_project_id.company_id:
#                 raise ValidationError(
#                     _('The Company in the Timesheet Sheet and in '
#                       'the Project must be the same.'))

#     @api.multi
#     @api.constrains('company_id', 'add_line_task_id')
#     def _check_company_id_add_line_task_id(self):
#         for rec in self.sudo():
#             if rec.company_id and rec.add_line_task_id.company_id and \
#                     rec.company_id != rec.add_line_task_id.company_id:
#                 raise ValidationError(
#                     _('The Company in the Timesheet Sheet and in '
#                       'the Task must be the same.'))

#     @api.multi
#     def _get_possible_reviewers(self):
#         self.ensure_one()
#         if self.review_policy == 'hr':
#             return self.env.ref('hr.group_hr_user').users
#         return self.env['res.users']

#     @api.multi
#     def _get_timesheet_sheet_company(self):
#         self.ensure_one()
#         employee = self.employee_id
#         company = employee.company_id or employee.department_id.company_id
#         if not company:
#             company = employee.user_id.company_id
#         return company

#     @api.onchange('employee_id')
#     def _onchange_employee_id(self):
#         if self.employee_id:
#             company = self._get_timesheet_sheet_company()
#             self.company_id = company
#             self.review_policy = company.timesheet_sheet_review_policy
#             self.department_id = self.employee_id.department_id

	def _get_timesheet_sheet_lines_domain(self):
		self.ensure_one()
		return [
			('date', '<=', self.date_end),
			('date', '>=', self.date_start),
			('employee_id', '=', self.employee_id.id),
			('company_id', '=', self._get_timesheet_sheet_company().id),
			('project_id', '!=', False),
			('timesheet_type_id', '!=', False)
		]
# #edited line here
#     @api.multi
#     @api.depends('date_start', 'date_end')
#     def _compute_line_ids(self):
#         SheetLine = self.env['hr_timesheet.sheet.line']
#         for sheet in self:
#             if not all([sheet.date_start, sheet.date_end]):
#                 continue
#             matrix = sheet._get_data_matrix()
#             vals_list = []
#             for key in sorted(matrix,
#                               key=lambda key: self._get_matrix_sortby(key)):
#                 vals_list.append(sheet._get_default_sheet_line(matrix, key))
#                 sheet.clean_timesheets(matrix[key])
				
#             sheet.line_ids = SheetLine.create(vals_list)

	@api.model
	def _matrix_key_attributes(self):
		""" Hook for extensions """
		return ['date', 'project_id', 'task_id', 'timesheet_type_id']

#     @api.model
#     def _matrix_key(self):
#         return namedtuple('MatrixKey', self._matrix_key_attributes())

	@api.model
	def _get_matrix_key_values_for_line(self, aal):
		""" Hook for extensions """
		return {
			'date': aal.date,
			'project_id': aal.project_id,
			'task_id': aal.task_id,
			'timesheet_type_id': aal.timesheet_type_id,
		}

#     @api.model
#     def _get_matrix_sortby(self, key):
#         res = []
#         for attribute in key:
#             value = None
#             if hasattr(attribute, 'name_get'):
#                 name = attribute.name_get()
#                 value = name[0][1] if name else ''
#             else:
#                 value = attribute
#             res.append(value)
#         return res

#     @api.multi
#     def _get_data_matrix(self):
#         self.ensure_one()
#         MatrixKey = self._matrix_key()
#         matrix = {}
#         empty_line = self.env['account.analytic.line']
#         for line in self.timesheet_ids:
#             key = MatrixKey(**self._get_matrix_key_values_for_line(line))
#             if key not in matrix:
#                 matrix[key] = empty_line
#             matrix[key] += line
#         for date in self._get_dates():
#             for key in matrix.copy():
#                 key = MatrixKey(**{
#                     **key._asdict(),
#                     'date': date,
#                 })
#                 if key not in matrix:
#                     matrix[key] = empty_line
#         return matrix

#     def _compute_timesheet_ids(self):
#         AccountAnalyticLines = self.env['account.analytic.line']
#         for sheet in self:
#             domain = sheet._get_timesheet_sheet_lines_domain()
#             timesheets = AccountAnalyticLines.search(domain)
#             sheet.link_timesheets_to_sheet(timesheets)
#             sheet.timesheet_ids = timesheets

#     @api.onchange('date_start', 'date_end', 'employee_id')
#     def _onchange_scope(self):
#         self._compute_timesheet_ids()

#     @api.onchange('date_start', 'date_end')
#     def _onchange_dates(self):
#         if self.date_start > self.date_end:
#             self.date_end = self.date_start

#     @api.onchange('timesheet_ids')
#     def _onchange_timesheets(self):
#         self._compute_line_ids()

#     @api.onchange('add_line_project_id')
#     def onchange_add_project_id(self):
#         """Load the project to the timesheet sheet"""
#         if self.add_line_project_id:
#             return {
#                 'domain': {
#                     'add_line_task_id': [
#                         ('project_id', '=', self.add_line_project_id.id),
#                         ('company_id', '=', self.company_id.id),
#                         ('id', 'not in',
#                          self.timesheet_ids.mapped('task_id').ids)],
#                 },
#             }
#         else:
#             return {
#                 'domain': {
#                     'add_line_task_id': [('id', '=', False)],
#                 },
#             }

#     @api.model
#     def _check_employee_user_link(self, vals):
#         if 'employee_id' in vals:
#             employee = self.env['hr.employee'].browse(vals['employee_id'])
#             if not employee.user_id:
#                 raise UserError(_(
#                     'In order to create a sheet for this employee, you must'
#                     ' link him/her to an user: %s'
#                 ) % (
#                     employee.name,
#                 ))
#             return employee.user_id.id
#         return False

#     @api.multi
#     def copy(self, default=None):
#         if not self.env.context.get('allow_copy_timesheet'):
#             raise UserError(_('You cannot duplicate a sheet.'))
#         return super().copy(default=default)

#     @api.model
#     def create(self, vals):
#         self._check_employee_user_link(vals)
#         res = super(Sheet,self).create(vals)
#         res.write({'state': 'draft'})   
#         return res

#     def _sheet_write(self, field, recs):
#         self.with_context(sheet_write=True).write({field: [(6, 0, recs.ids)]})

#     @api.multi
#     def write(self, vals):
#         self._check_employee_user_link(vals)
#         res = super(Sheet,self).write(vals)
#         for rec in self:
#             if rec.state == 'draft' and \
#                     not self.env.context.get('sheet_write'):
#                 rec._update_analytic_lines_from_new_lines(vals)
#                 if 'add_line_project_id' not in vals:
#                     rec.delete_empty_lines(True)
#         return res

#     @api.multi
#     def unlink(self):
#         for sheet in self:
#             if sheet.state in ('confirm', 'done'):
#                 raise UserError(_(
#                     'You cannot delete a timesheet sheet which is already'
#                     ' submitted or confirmed: %s') % (
#                         sheet.complete_name,
#                     ))
#         return super().unlink()

#     def _get_informables(self):
#         """ Hook for extensions """
#         self.ensure_one()
#         return self.employee_id.parent_id.user_id.partner_id

#     def _timesheet_subscribe_users(self):
#         for sheet in self.sudo():
#             subscribers = sheet._get_possible_reviewers().mapped('partner_id')
#             subscribers |= sheet._get_informables()
#             if subscribers:
#                 self.message_subscribe(partner_ids=subscribers.ids)

#     @api.multi
#     def action_timesheet_draft(self):
#         if self.filtered(lambda sheet: sheet.state not in ['done','refuse']):
#             raise UserError(_('Cannot revert to draft a non-approved sheet.'))
#         self._check_can_review()
#         self.write({
#             'state': 'draft',
#             'reviewer_id': False,
#         })
#         model = self.env['timesheet.project.manager.check']
#         lines = model.search([('sheet_id', '=', self.id)])
#         if len(lines) > 0:
#             for i in lines:
#                 model.search([('id', '=', i.id)]).unlink()

	def action_timesheet_confirm(self):
		type_ids = self.env['hr.timesheet.type'].search([])
		for type in type_ids:
#             timesheet_ids = self.env['account.analytic.line'].search([('sheet_id', '=', self.id), ('timesheet_type_id', '=', type.id)])
			for n in range(int ((self.date_end - self.date_start).days) + 1):
				amount = 0.0
				timesheet_ids = self.env['account.analytic.line'].search([('date', '=', self.date_start + timedelta(n)), ('employee_id', '=', self.employee_id.id), ('timesheet_type_id', '=', type.id), ('sheet_state', '!=', 'refuse')])
				amount = round(sum(timesheet_ids.mapped('unit_amount')), 2)
				if amount > type.max_hrs:
					raise UserError(_('Your time exceeds the maximum hour for type %s. Please edit the time') % (type.name))
#         self._timesheet_subscribe_users()
		self.reset_add_line()
		project_ids = [line.project_id.user_id for line in self.timesheet_ids]
		new_project_ids = list(set(project_ids))
		for project in new_project_ids:
			if project.id:
				vals = {
					'user_id' : project.id,
					'is_validated': False,
					'sheet_id' : self.id
					}
				self.env['timesheet.project.manager.check'].create(vals)
		self.write({'state': 'confirm'})
		# template_id = self.env.ref('hr_timesheet_sheet.hr_tmesheet_for_reporting_manager_templates')
		# timesheet_action = self.env.ref('hr_timesheet_sheet.act_hr_timesheet_sheet_to_review_for_report_manager')
		# rendering_context = dict(self._context)
		# rendering_context.update({
			
		# 	'action_id': timesheet_action.id,
		# 	'dbname': self._cr.dbname,
		# 	'model': 'hr_timesheet.sheet',
		# 	'view_type' : 'form',
		# 	'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
		# 	'force_event_id': self.id,
 
		# })
		# if template_id:
		# 	template_id.with_context(rendering_context).send_mail(self.id,force_send=True)

	

#     @api.multi
#     def action_timesheet_pmconfirm(self):
#         self.write({'state': 'pmconfirm'})
#         template_id = self.env.ref('hr_timesheet_sheet.hr_tmesheet_for_project_manager_template')
#         emails = ""
#         for project in self.project_manager_check_ids:
#             emails += project.user_id.email + ','
#         timesheet_action = self.env.ref('hr_timesheet_sheet.act_hr_timesheet_sheet_to_review_for_report_manager')
#         rendering_context = dict(self._context)
#         rendering_context.update({
		   
#             'action_id': timesheet_action.id,
#             'dbname': self._cr.dbname,
#             'model': 'hr_timesheet.sheet',
#             'view_type' : 'form',
#             'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
#             'force_event_id': self.id,

#         })
#         if template_id:
#             template_id.email_to = emails
#             template_id.with_context(rendering_context).send_mail(self.id,force_send=True)

	
#     @api.multi
#     def action_timesheet_done(self):
#         if self.filtered(lambda sheet: sheet.state != 'pmconfirm'):
#             raise UserError(_('Cannot approve a non-submitted sheet.'))
#         self._check_can_review()
#         for line in self.project_manager_check_ids:
#             if self.env.user.has_group('hr_timesheet_sheet.group_super_manager'):
#                 lines = self.env['timesheet.project.manager.check'].search([('sheet_id', '=', self.id)])
#                 for i in lines:
#                     i.update({
#                     'is_validated': True,
#                     })
#             if line.user_id.id == self.env.user.id:
#                 lines = self.env['timesheet.project.manager.check'].search([('sheet_id', '=', self.id), ('user_id', '=', self.env.user.id)])
#                 lines.update({
#                     'is_validated': True,
#                 })
#         false_lines = self.env['timesheet.project.manager.check'].search([('sheet_id', '=', self.id), ('is_validated', '=', False)])
#         if len(false_lines) == 0:
#             self.write({
#                 'state': 'done',
#                 'reviewer_id': self._get_current_reviewer().id,
#                 })
#         template_id = self.env.ref('hr_timesheet_sheet.hr_tmesheet_for_done_manager_templates')
#         timesheet_action = self.env.ref('hr_timesheet_sheet.act_hr_timesheet_sheet_to_review_for_report_manager')

#         rendering_context = dict(self._context)
#         rendering_context.update({
		   
#             'action_id': timesheet_action.id,
#             'dbname': self._cr.dbname,
#             'model': 'hr_timesheet.sheet',
#             'view_type' : 'form',
#             'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
#             'force_event_id': self.id,

#         })
#         if template_id:
			
#             template_id.with_context(rendering_context).send_mail(self.id,force_send=True)
		

#     @api.multi
#     def action_timesheet_refuse(self):
#         if self.filtered(lambda sheet: sheet.state not in ['confirm','pmconfirm']):
#             raise UserError(_('Cannot reject a non-submitted sheet.'))
#         self._check_can_review()
#         self.write({
#             'state': 'refuse',
#             'reviewer_id': False,
#         })
#         model = self.env['timesheet.project.manager.check']
#         lines = model.search([('sheet_id', '=', self.id)])
#         if len(lines) > 0:
#             for i in lines:
#                 model.search([('id', '=', i.id)]).unlink()

#     @api.multi
#     def action_timesheet_refuse1(self):
#         if self.filtered(lambda sheet: sheet.state not in ['confirm','pmconfirm']):
#             raise UserError(_('Cannot reject a non-submitted sheet.'))
#         self._check_can_review()
#         self.write({
#             'state': 'refuse',
#             'reviewer_id': False,
#         })
#         model = self.env['timesheet.project.manager.check']
#         lines = model.search([('sheet_id', '=', self.id)])
#         if len(lines) > 0:
#             for i in lines:
#                 model.search([('id', '=', i.id)]).unlink()

#     @api.model
#     def _get_current_reviewer(self):
#         reviewer = self.env['hr.employee'].search(
#             [('user_id', '=', self.env.uid)],
#             limit=1
#         )
#         if not reviewer:
#             raise UserError(_(
#                 'In order to review a timesheet sheet, your user needs to be'
#                 ' linked to an employee.'
#             ))
#             pass
#         return reviewer

#     @api.multi
#     def _check_can_review(self):
#         if self.filtered(
#                 lambda x: not x.can_review and x.review_policy == 'hr'):
#             pass
# #             raise UserError(_(
# #                 'Only a HR Officer or Manager can review the sheet.'
# #             ))

#     @api.multi
#     def button_add_line(self):
#         for rec in self:
#             if rec.state in ['new', 'draft']:
#                 rec.add_line()
#                 rec.reset_add_line()

#     def reset_add_line(self):
#         self.write({
#             'add_line_project_id': False,
#             'add_line_task_id': False,
#         })

#     def _get_date_name(self, date):
#         name = babel.dates.format_skeleton(
#             skeleton='MMMEd',
#             datetime=datetime.combine(date, time.min),
#             locale=(
#                 self.env.context.get('lang') or self.env.user.lang or 'en_US'
#             ),
#         )
#         name = re.sub(r'(\s*[^\w\d\s])\s+', r'\1\n', name)
#         name = re.sub(r'([\w\d])\s([\w\d])', u'\\1\u00A0\\2', name)
#         return name

#     def _get_dates(self):
#         start = self.date_start
#         end = self.date_end
#         if end < start:
#             return []
#         dates = [start]
#         while start != end:
#             start += relativedelta(days=1)
#             dates.append(start)
#         return dates

# 	def _get_line_name(self, project_id, task_id=None, timesheet_type_id=None, **kwargs):
# 		timesheets_line = self.timesheet_ids
# 		self.ensure_one()
# 		if task_id:
# 			return '%s - %s - %s' % (project_id.name, task_id.name, timesheet_type_id.name)
# 		if type(project_id) is dict:
# 			return '%s - %s' % (project_id.get('project_id') and project_id.get('project_id').name, project_id.get('timesheet_type_id') and  project_id.get('timesheet_type_id').name)
# 		if timesheet_type_id:
# 			return project_id.name + ' - '+timesheet_type_id.name
	
		

# 	def _get_new_line_name_values(self):
# 		""" Hook for extensions """
# 		self.ensure_one()
# #         edited line here
# 		return {
# 			'project_id': self.add_line_project_id,
# 			'task_id': self.add_line_task_id,
# 			# 'timesheet_type_id': self.add_line_timesheet_type_id,
# 		}
	def _get_default_sheet_line(self, matrix, key):
		self.ensure_one()
		values = {
			"value_x": self._get_date_name(key.date),
			"value_y": self._get_line_name(**key._asdict()),
			"date": key.date,
			"project_id": key.project_id.id,
			"task_id": key.task_id.id,
			"unit_amount": sum(t.unit_amount for t in matrix[key]),
			"employee_id": self.employee_id.id,
			"company_id": self.company_id.id,
			'timesheet_type_id': key.timesheet_type_id.id,
		}
		if self.id:
			values.update({"sheet_id": self.id})
		return values

#     @api.multi
#     def _get_default_sheet_line(self, matrix, key):
#         self.ensure_one()
#         values = {
#             'value_x': self._get_date_name(key.date),
#             'value_y': self._get_line_name(**key._asdict()),
#             'date': key.date,
#             'project_id': key.project_id.id,
#             'task_id': key.task_id.id,
#             'unit_amount': sum(t.unit_amount for t in matrix[key]),
#             'employee_id': self.employee_id.id,
#             'company_id': self.company_id.id,
#             'timesheet_type_id': key.timesheet_type_id.id,
#         }
#         if self.id:
#             values.update({'sheet_id': self.id})
#         return values
	
	
# edited line here
	# @api.model
	# def _prepare_empty_analytic_line(self):
	#     return {
	#         'name': empty_name,
	#         'employee_id': self.employee_id.id,
	#         'date': self.date_start,
	#         'project_id': self.add_line_project_id.id,
	#         'task_id': self.add_line_task_id.id,
	#         'timesheet_type_id' : self.add_line_timesheet_type_id.id,
	#         'sheet_id': self.id,
	#         'unit_amount': 0.0,
	#         'company_id': self.company_id.id,
	#     }
	@api.model
	def _prepare_empty_analytic_line(self):
		return {
			"name": empty_name,
			"employee_id": self.employee_id.id,
			"date": self.date_start,
			"project_id": self.add_line_project_id.id,
			"task_id": self.add_line_task_id.id,
			"sheet_id": self.id,
			# 'timesheet_type_id' : self.add_line_timesheet_type_id.id,
			"unit_amount": 0.0,
			"company_id": self.company_id.id,
		}


	# def add_line(self):
	#     if self.add_line_project_id:
	#         values = self._prepare_empty_analytic_line()
	#         name_line = self._get_line_name(
	#             self._get_new_line_name_values()
	#         )
	#         name_list = list(set(self.line_ids.mapped('value_y')))
	#         if name_list:
	#             self.delete_empty_lines(False)
	#         if name_line not in name_list:
	#             self.timesheet_ids |= \
	#                 self.env['account.analytic.line']._sheet_create(values)

	# def link_timesheets_to_sheet(self, timesheets):
	#     self.ensure_one()
	#     if self.id and self.state in ['new', 'draft']:
	#         for aal in timesheets.filtered(lambda a: not a.sheet_id):
	#             aal.write({'sheet_id': self.id})

	# def clean_timesheets(self, timesheets):
	#     repeated = timesheets.filtered(lambda t: t.name == empty_name)
	#     if len(repeated) > 1 and self.id:
	#         return repeated.merge_timesheets()
	#     return timesheets

	# @api.multi
	# def _is_add_line(self, row):
	#     """ Hook for extensions """
	#     self.ensure_one()
	#     return self.add_line_project_id == row.project_id \
	#         and self.add_line_task_id == row.task_id

	# @api.model
	# def _is_line_of_row(self, aal, row):
	#     """ Hook for extensions """
	#     return aal.project_id.id == row.project_id.id \
	#         and aal.task_id.id == row.task_id.id

	# def delete_empty_lines(self, delete_empty_rows=False):
	#     self.ensure_one()
	#     for name in list(set(self.line_ids.mapped('value_y'))):
	#         rows = self.line_ids.filtered(lambda l: l.value_y == name)
	#         if not rows:
	#             continue
	#         row = fields.first(rows)
	#         if delete_empty_rows and self._is_add_line(row):
	#             check = any([l.unit_amount for l in rows])
	#         else:
	#             check = not all([l.unit_amount for l in rows])
	#         if not check:
	#             continue
	#         row_lines = self.timesheet_ids.filtered(
	#             lambda aal: self._is_line_of_row(aal, row)
	#         )
	#         row_lines.filtered(
	#             lambda t: t.name == empty_name and not t.unit_amount
	#         ).unlink()
	#         if self.timesheet_ids != self.timesheet_ids.exists():
	#             self._sheet_write(
	#                 'timesheet_ids', self.timesheet_ids.exists())

	# @api.multi
	# def _update_analytic_lines_from_new_lines(self, vals):
	#     self.ensure_one()
	#     new_line_ids_list = []
	#     for line in vals.get('line_ids', []):
	#         # Every time we change a value in the grid a new line in line_ids
	#         # is created with the proposed changes, even though the line_ids
	#         # is a computed field. We capture the value of 'new_line_ids'
	#         # in the proposed dict before it disappears.
	#         # This field holds the ids of the transient records
	#         # of model 'hr_timesheet.sheet.new.analytic.line'.
	#         if line[0] == 1 and line[2] and line[2].get('new_line_id'):
	#             new_line_ids_list += [line[2].get('new_line_id')]
	#     for new_line in self.new_line_ids.exists():
	#         if new_line.id in new_line_ids_list:
	#             new_line._update_analytic_lines()
	#     self.new_line_ids.exists().unlink()
	#     self._sheet_write('new_line_ids', self.new_line_ids.exists())

	@api.model
	def _prepare_new_line(self, line):
		""" Hook for extensions """
		line_id = line.sheet_id.id
		project = line.project_id.id
		task = line.task_id.id
		model = self.env['hr_timesheet.sheet.line']
		type_id_line = model.search([('sheet_id', '=', line_id), ('project_id', '=', project), ('task_id', '=', task), ('timesheet_type_id', '!=', False)], limit=1)
		for item in type_id_line:
			type = item.timesheet_type_id.id
		
		return {
			'sheet_id': line.sheet_id.id,
			'date': line.date,
			'project_id': line.project_id.id,
			'task_id': line.task_id.id,
			'unit_amount': line.unit_amount,
			'company_id': line.company_id.id,
			'employee_id': line.employee_id.id,
			'timesheet_type_id': line.timesheet_type_id.id,
		}

	# @api.multi
	# def _is_compatible_new_line(self, line_a, line_b):
	#     """ Hook for extensions """
	#     self.ensure_one()
	#     return line_a.project_id.id == line_b.project_id.id \
	#         and line_a.task_id.id == line_b.task_id.id \
	#         and line_a.date == line_b.date

	# @api.multi
	# def add_new_line(self, line):
	#     self.ensure_one()
	#     new_line_model = self.env['hr_timesheet.sheet.new.analytic.line']
	#     new_line = self.new_line_ids.filtered(
	#         lambda l: self._is_compatible_new_line(l, line)
	#     )
	#     if new_line:
	#         new_line.write({'unit_amount': line.unit_amount})
	#     else:
	#         vals = self._prepare_new_line(line)
	#         new_line = new_line_model.create(vals)
	#     self._sheet_write('new_line_ids', self.new_line_ids | new_line)
	#     line.new_line_id = new_line.id

	# ------------------------------------------------
	# OpenChatter methods and notifications
	# ------------------------------------------------

#     @api.multi
#     def _track_subtype(self, init_values):
#         if self:
#             record = self[0]
# #             if 'state' in init_values and record.state == 'confirm':
# #                 return 'hr_timesheet_sheet.mt_timesheet_confirmed'
#             if 'state' in init_values and record.state == 'done':
#                 return 'hr_timesheet_sheet.mt_timesheet_approved'
#         return super()._track_subtype(init_values)


class AbstractSheetLine(models.AbstractModel):
	_inherit = 'hr_timesheet.sheet.line.abstract'
	_description = 'Abstract Timesheet Sheet Line'

	
	timesheet_type_id = fields.Many2one(
		comodel_name='hr.timesheet.type',
	)


class SheetLine(models.TransientModel):
	_inherit = 'hr_timesheet.sheet.line'
	_description = 'Timesheet Sheet Line'

	
	timesheet_type_id = fields.Many2one(
		comodel_name='hr.timesheet.type',
	)

	# @api.onchange('unit_amount')
	# def onchange_unit_amount(self):
	#     """ This method is called when filling a cell of the matrix. """
	#     self.ensure_one()
	#     sheet = self._get_sheet()
	#     if not sheet:
	#         return {'warning': {
	#             'title': _("Warning"),
	#             'message': _("Save the Timesheet Sheet first."),
	#         }}
	#     sheet.add_new_line(self)

	# @api.model
	# def _get_sheet(self):
	#     sheet = self.sheet_id
	#     if not sheet:
	#         model = self.env.context.get('params', {}).get('model', '')
	#         obj_id = self.env.context.get('params', {}).get('id')
	#         if model == 'hr_timesheet.sheet' and isinstance(obj_id, int):
	#             sheet = self.env['hr_timesheet.sheet'].browse(obj_id)
	#     return sheet


class SheetNewAnalyticLine(models.TransientModel):
	_inherit = 'hr_timesheet.sheet.new.analytic.line'
	_description = 'Timesheet Sheet New Analytic Line'

	timesheet_type_id = fields.Many2one(
		comodel_name='hr.timesheet.type',
	)

	@api.model
	def _is_similar_analytic_line(self, aal):
		""" Hook for extensions """
		return aal.date == self.date \
			and aal.project_id.id == self.project_id.id \
			and aal.task_id.id == self.task_id.id \
			and aal.timesheet_type_id.id == self.timesheet_type_id.id

	@api.model
	def _update_analytic_lines(self):
		sheet = self.sheet_id
		timesheets = sheet.timesheet_ids.filtered(
			lambda aal: self._is_similar_analytic_line(aal)
		)
		new_ts = timesheets.filtered(lambda t: t.name == empty_name)
		
		new_ts_values = sheet._prepare_new_line(self)
		
		
		
		amount = sum(t.unit_amount for t in timesheets)
		diff_amount = self.unit_amount - amount
		if len(new_ts) > 1:
			new_ts = new_ts.merge_timesheets()
			sheet._sheet_write('timesheet_ids', sheet.timesheet_ids.exists())
		if not diff_amount:
			return
		if new_ts:
			
			
			
			unit_amount = new_ts.unit_amount + diff_amount
			if unit_amount:
				
				new_ts.write({'unit_amount': unit_amount, 'timesheet_type_id':new_ts_values['timesheet_type_id']})
			else:
				
				new_ts.unlink()
				sheet._sheet_write(
					'timesheet_ids', sheet.timesheet_ids.exists())
		else:
			
			
			
			new_ts_values = sheet._prepare_new_line(self)
			new_ts_values.update({
				'name': empty_name,
				'unit_amount': diff_amount,
			})
		   
			self.env['account.analytic.line']._sheet_create(new_ts_values)
