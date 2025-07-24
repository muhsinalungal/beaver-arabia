# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class Estimate(models.Model):
    _name = "sale.estimate.project"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']  # odoo11
    _description = "Sales Estimate Job"
    _rec_name = "name"

    
    name = fields.Char('Number', copy=True, default=lambda self: _('New'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Estimate Sent'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('versioned', 'Versioned'),
        ('quotesend', 'Quotation Created'),
        ('cancel', 'Cancelled')],
        default='draft',
        track_visibility='onchange',
        copy='False',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=False,
    )
    description = fields.Text(
        string='Description of Work'
    )
    note = fields.Text(
        string='Note'
    )
    reference = fields.Char(
        string='Customer Reference')

    division_id = fields.Many2one(
        comodel_name="site.site",
        string="Division",)
    rfq_ref = fields.Char(string="RFQ Ref",readonly=True)
    contact_no = fields.Char(string="Contract No",)
    tender_no = fields.Char(string="Tender No",)
    job_desc = fields.Char(string="Job Description",)
    estimate_date = fields.Date(
        'Date',
        required=True,
        copy=True,
        default=fields.date.today(),
    )
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.user.company_id,
        string='Company',
    )
    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Pricelist',
        help="Pricelist for current sales estimate."
    )
    currency_id = fields.Many2one(
        "res.currency",
        related='pricelist_id.currency_id',
        string="Currency",
        readonly=True,
        # required=True,
        store=True,
    )
    user_id = fields.Many2one(
        'res.users',
        'Sales Person',
        default=lambda self: self.env.user,
    )
    estimate_ids = fields.One2many(
        'estimate.project',
        'estimate_id',
        'Estimate',
        copy=True,
    )
    version_number = fields.Float(
        string="Version Number",default=0.0)
    parent_version_id = fields.Many2one(
        'sale.estimate.project',
        string='Parent Version',
        )
    parent_version_name = fields.Char('parent_version_name')
    child_version_number = fields.Float(
        string="Child Version Number",default=0.0)
    project_ref_id = fields.Many2one('project.project',string='Project Ref.')
    email_from = fields.Char('Email', tracking=40, index=True,compute='_compute_email_from',readonly=False, store=True)
    phone = fields.Char('Phone', tracking=50,compute='_compute_phone', readonly=False, store=True)

    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string='Fiscal Position',
        domain="[('company_id', '=', company_id)]", check_company=True)
    estimate_line_count = fields.Integer(string='Estimate Line Count', compute='get_estimate_line_count', readonly=True)



    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('product.estimate.seq.job') or _('New')
        return super(Estimate, self).create(vals)

    def action_view_estimates(self):
        estimates = self.mapped('estimate_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('bt_job_cost_estimation.action_project')
        action['context'] = {'default_estimate_id': self.id, 'default_currency_id': self.currency_id.id}
        action['domain'] = [('id', 'in', estimates.ids)]
        return action

    def get_estimate_line_count(self):
        for rec in self:
            estimate_lines = self.env['estimate.project'].search([('estimate_id', "=", rec.id)])
            rec.write({'estimate_line_count': len(estimate_lines)})

    def estimate_send(self):
        for rec in self:
            rec.state = 'sent'

    def estimate_confirm(self):
        for rec in self:
            if not rec.estimate_ids:
                raise UserError(_('Please enter Estimation Lines!'))
            # if rec.estimate_line_ids:
            #     for line in rec.estimate_line_ids:
            #         if line.pricelist_active!=True:
            #             raise UserError(_('Please Update the Product Price.'))
            rec.state = 'confirm'

    def estimate_approve(self):
        for rec in self:
            rec.state = 'approve'

    def estimate_quotesend(self):
        for rec in self:
            rec.state = 'quotesend'

    def estimate_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def estimate_reject(self):
        for rec in self:
            rec.state = 'reject'

    def reset_todraft(self):
        for rec in self:
            rec.state = 'draft'

    def action_estimate_send(self):
        pass

    def estimate_to_quotation(self):
        return

    def contract_close(self):
        return
    
    
    def estimate_versioned(self):
        for rec in self:
            if not rec.parent_version_id:
                parent_version_name=rec.name + '_V'
                rec.parent_version_name=parent_version_name
            else:
                parent_version_name=rec.parent_version_name
            
            child_version_number=rec.child_version_number
            new_child_version_number=child_version_number+1
            rec.child_version_number=new_child_version_number
            name=parent_version_name+str(new_child_version_number)
            child_parent_version_name=name
            estimate = rec.copy()
            estimate.write({'name':name,'parent_version_name':child_parent_version_name,'state':'draft','parent_version_id':rec.id,'child_version_number':0.0})
            rec.state='versioned'
            return estimate