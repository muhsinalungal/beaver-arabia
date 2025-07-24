# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError , AccessError





class ResSalesPerson(models.Model):
	_name = "res.salesperson"

	name = fields.Char(index=True)
	image_1920 = fields.Image("Variant Image", max_width=1920, max_height=1920)

	employee_id = fields.Many2one('hr.employee', string='Related Employee', index=True)
	ref = fields.Char(string='Reference', index=True)
	vat = fields.Char(string='Tax ID', index=True,help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.")
	bank_ids = fields.One2many('res.partner.bank', 'partner_id', string='Banks')
	website = fields.Char('Website Link')
	comment = fields.Text(string='Notes')
	active = fields.Boolean(default=True)
	employee = fields.Many2one('hr.employee',help="Check this box if this contact is an Employee.")
	function = fields.Char(string='Job Position')
	street = fields.Char()
	street2 = fields.Char()
	zip = fields.Char(change_default=True)
	city = fields.Char()
	state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
							   domain="[('country_id', '=?', country_id)]")
	country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
	partner_latitude = fields.Float(string='Geo Latitude', digits=(16, 5))
	partner_longitude = fields.Float(string='Geo Longitude', digits=(16, 5))
	email = fields.Char()
	phone = fields.Char()
	mobile = fields.Char()

	company_name = fields.Char('Company Name')
	barcode = fields.Char(help="Use a barcode to identify this contact.", copy=False, company_dependent=True)

	@api.onchange('employee')
	def onchange_employee(self):
		for record in  self:
			if record.employee:
				record.name = record.employee.name
				if record.employee.address_id:
					record.street = record.employee.address_id.street
					record.street2 = record.employee.address_id.street2
					record.city = record.employee.address_id.city
					record.mobile = record.employee.mobile_phone
					record.phone = record.employee.work_phone
					record.email = record.employee.work_email







