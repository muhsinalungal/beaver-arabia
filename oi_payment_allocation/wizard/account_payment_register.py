'''
Created on Oct 20, 2019

@author: Zuhair Hammadi
'''
from odoo import models, fields, api , _
from odoo.exceptions import ValidationError

class AccountPaymentRegister(models.TransientModel):
	_inherit= 'account.payment.register'

	@api.model
	def default_get(self, fields_list):
		# OVERRIDE
		res = super().default_get(fields_list)
		return res


class PaymentRegisterLines(models.Model):
	_name = "account.payment.register.line"
	_description ='Payment Allocation Line'
	
	# allocation_id = fields.Many2one('account.payment.allocation', required = False, ondelete='cascade')
	type = fields.Selection([('invoice', 'Invoice'),('credit', 'Credit Invoice'),('debit', 'Debit Invoice'), ('payment', 'Payment'), ('other', 'Other'),('advance', 'Advance')])
	
	move_line_id = fields.Many2one('account.move.line', required = True, ondelete = 'cascade')
   
	company_currency_id = fields.Many2one(related='move_line_id.company_currency_id')
	currency_id = fields.Many2one(related='move_line_id.company_currency_id')
	amount_residual = fields.Monetary(related='move_line_id.amount_residual')
	partner_id = fields.Many2one(related='move_line_id.partner_id')
	ref = fields.Char(related='move_line_id.ref', readonly = True)
	name = fields.Char(related='move_line_id.name', readonly = True)
	date_maturity = fields.Date(related='move_line_id.date_maturity', readonly = True)
	date = fields.Date(related='move_line_id.date', readonly = True)
		
	allocate = fields.Boolean()
	allocate_amount = fields.Monetary()
	
	invoice_id = fields.Many2one(related='move_line_id.move_id', readonly = True)
	payment_id = fields.Many2one(related='move_line_id.payment_id', readonly = True, string='Payment')
	move_id = fields.Many2one(related='move_line_id.move_id', readonly = True)
	balance = balance = fields.Monetary(related='move_line_id.balance', readonly = True)
	
	payment_date = fields.Date(related='payment_id.date', readonly = True)
	payment_amount = fields.Monetary(compute = '_calc_payment_amount')
	communication = fields.Char(related='payment_id.ref', readonly = True)
	
	date_invoice = fields.Date(related='invoice_id.invoice_date', readonly = True)
	invoice_amount = fields.Monetary(compute = "_calc_invoice_amount")
	
	amount_residual_display = fields.Monetary(compute = '_calc_amount_residual_display', string='Unallocated Amount')
	
	sign = fields.Integer(compute = "_calc_sign")
	payment_id = fields.Many2one('account.payment',)