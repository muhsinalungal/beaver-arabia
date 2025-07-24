# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class sale_estimate_details(models.Model):
    _name = "sale.estimate.details"
    
    name = fields.Char('Name',)
    number = fields.Float(string='Number')
    length1 = fields.Float(string='Length')
    width = fields.Float(string='Width')
    height = fields.Float(string='Height')
    quantity = fields.Float(string='Quantity')
    coefficient = fields.Float(string='Coefficient')
    estimate_id = fields.Many2one('sale.estimate',string='Sale Estimate',ondelete='cascade')
    uom_id = fields.Many2one('uom.uom','Unit',)
    project_id = fields.Many2one('sale.project',string='Project',)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Estimate Sent'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('quotesend', 'Quotation Created'),
        ('cancel', 'Cancelled')],
        default='draft', related='project_id.state',store=True)

    # project_ref = fields.Many2one('sale.project',string='Project')
    remarks = fields.Text('Remarks',)
                
    @api.onchange('number','length1','width','height','coefficient')
    def _onchange_values(self):
        for rec in self:
            if rec.number ==0.00:
                number=1
            else:
                 number=rec.number
            if rec.length1 ==0.00:
                length=1
            else:
                 length=rec.length1
            if rec.width ==0.00:
                width=1
            else:
                 width=rec.width   
            if rec.height ==0.00:
                height=1
            else:
                 height=rec.height  
            if rec.coefficient ==0.00:
                coefficient=1
            else:
                 coefficient=(rec.coefficient/100)* 7850        
            rec.quantity = number * length * width * height * coefficient        
                
            
    @api.onchange('estimate_id')
    def _onchange_estimate_id(self):
        if self.estimate_id:
            self.uom_id = self.estimate_id.work_uom_id.id
    @api.onchange('name')
    def _onchange_name(self):
        
        self.uom_id = self.estimate_id.work_uom_id
        self.project_id = self.env.context['active_id']

    @api.model
    def create(self, vals):
        if vals.get('estimate_id'):
            estimate = self.env['sale.estimate'].browse(vals['estimate_id'])
            if estimate.project_id:
                vals['project_id'] =estimate.project_id.id
        detail = super(sale_estimate_details, self).create(vals)
        return detail

    def write(self, vals):
        if 'estimate_id' in vals:
            estimate_id = vals.get('estimate_id') or self.estimate_id.id
            if estimate_id:
                estimate=self.env['sale.estimate'].browse(estimate_id)
                if estimate.project_id:
                    vals['project_id'] = estimate.project_id.id
        
        res = super(sale_estimate_details, self).write(vals)
        
        return res
