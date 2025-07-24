# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning



class CrmLead(models.Model):
	_inherit = "crm.lead"

	division_id = fields.Many2one(
		comodel_name="site.site",
		string="Division",)
	rfq_ref = fields.Char(string="RFQ Ref")
	estimate_count = fields.Integer('# Estimates', compute='_compute_estimate_count')
	estimate_ids = fields.One2many('sale.estimate','lead_id','Estimate')


	def _compute_estimate_count(self):
		if self.ids:
			estimate_data = self.env['sale.estimate'].sudo().read_group([
				('lead_id', 'in', self.ids)
			], ['lead_id'], ['lead_id'])
			mapped_data = {m['lead_id'][0]: m['lead_id_count'] for m in estimate_data}
		else:
			mapped_data = dict()
		for lead in self:
			lead.estimate_count = mapped_data.get(lead.id, 0)
			
	def crm_lead_estimate_action(self):
		action = self.env["ir.actions.actions"]._for_xml_id("bt_job_cost_estimation.action_sale_estimate_detail")
		action['context'] = {
			'search_default_partner_id': self.partner_id.id,
			'default_partner_id': self.partner_id.id,
			'default_lead_id': self.id,
			'default_contact_name': self.partner_name,
			# 'default_enquiry_location': self.enquiry_location,
			# 'default_project_location': self.project_location,
			'default_user_id': self.user_id.id,
			'default_division_id': self.division_id.id,
			'default_rfq_ref': self.rfq_ref,
		}
		action['domain'] = [('lead_id', '=', self.id)]
#         estimates = self.mapped('estimate_ids').filtered(lambda l: l.state in ('draft', 'sent'))
#         if len(estimates) == 1:
#             action['views'] = [(self.env.ref('bt_job_cost_estimation.form_view_project').id, 'form')]
#             action['res_id'] = estimates.id
		return action 

	@api.model
	def create(self, vals):
		
		vals["rfq_ref"] = (
				self.env["ir.sequence"].next_by_code("rfq.ref") or "New"
			)
		return super(CrmLead, self).create(vals) 

	def action_negotiate(self):
		self.stage_id = self.env['crm.stage'].search([('name', '=', 'Negotiated')]).id
		self.negotiated = True
		return True   


class sale_estimate_project(models.Model):
	_inherit = "sale.estimate"
	
	
	lead_id = fields.Many2one('crm.lead',string='Lead Ref.')
	# enquiry_location = fields.Char('Location of Enquiry')
	# project_location = fields.Char('Location of Project')
	# contact_name = fields.Char('Contact Name')
	# franchise_id = fields.Many2one("res.company", related='lead_id.franchise_id', string='Assigned Franchise', readonly=True, store=True)

	@api.model
	def default_get(self, fields):
		res = super(sale_estimate_project, self).default_get(fields)  
		ctx = dict(self.env.context)
		if ctx.get('partner_id'):
			res.update({
				'partner_id': ctx.get('partner_id')})
		if ctx.get('contact_name'):
		    res.update({
		        'contact_name': ctx.get('contact_name')})
		# if ctx.get('enquiry_location'):
		#     res.update({
		#         'enquiry_location': ctx.get('enquiry_location')})
		# if ctx.get('project_location'):
		#     res.update({
		#         'project_location': ctx.get('project_location')})
			   
		return res

