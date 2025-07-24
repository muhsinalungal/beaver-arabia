# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta


class Estimateline(models.Model):
    _name = "sale.estimate.line"
    _check_company_auto = True
    
    name = fields.Char('Name',)

    description = fields.Char('Description',)


    product_id = fields.Many2one(
        'product.product',
        string='Product',

    )


    product_qty = fields.Float(
        string='Quantity',
        default=1.0
    )

    product_uom_id = fields.Many2one(
        'uom.uom',
        string='UoM',
        domain="[('category_id', '=', product_uom_category_id)]"
    )
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    subtotal = fields.Float(
        'Subtotal',
        store=True,readonly=True
    )
    
    line_total = fields.Float(
        'Total',
        compute='_compute_amount',
        store=True,readonly=True
    )
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)

    project_id = fields.Many2one(
        'estimate.sheet',
        string='Project',
    )

    price_unit = fields.Float(
        'Rate',
        default=0.0,
    )
    
    product_description = fields.Text(
        string='Note',)

    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes',
        help="Taxes that apply on the base amount",
        check_company=True
    )
    company_id = fields.Many2one(
        'res.company', 'Company', index=True,
        default=lambda self: self.env.company)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Estimate Sent'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('quotesend', 'Quotation Created'),
        ('cancel', 'Cancelled')],
        default='draft', related='project_id.state',store=True)
    
    pricelist_id = fields.Many2one(related='project_id.pricelist_id', store=True,string='Pricelist',)
    # price_list_price = fields.Float('Price list price',compute='_compute_price_list',store=True)
    pricelist_active = fields.Boolean(default=True)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    duration = fields.Float('Duration',default=lambda self: self.project_id.duration_micro)
    estimate_type = fields.Selection(
        selection=[('wages','Wages'),
                    ('equipment','Equipments'),
                    ('material','Materials'),
                    ('general','General/Subcontractors')
                ],
        string="Type",
        required=True,)
    
    
    def _compute_tax_id(self):
        for line in self:
            line = line.with_company(line.company_id)
            fpos = line.project_id.fiscal_position_id or line.project_id.fiscal_position_id.get_fiscal_position(line.project_id.partner_id.id)
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda t: t.company_id == line.env.company)
            line.tax_ids = fpos.map_tax(taxes, line.product_id, line.project_id.partner_id)


    
    @api.onchange('product_id')
    def product_id_change(self):
        for rec in self:
            if rec.product_id:
                rec.description = rec.product_id.name
                rec.product_uom_id = rec.product_id.uom_id.id
                rec.price_unit = rec.product_id.lst_price
              
            else:
                self.price_unit = 0.0
                self.description = ""
                self.product_uom_id = False

    @api.onchange('price_unit','product_qty','duration')
    def price_unit_change(self):
        for rec in self:
            rec.subtotal = rec.price_unit * rec.duration * rec.product_qty
          
                
              
        
           
    
            
            
    @api.depends('product_qty', 'price_unit')
    def _compute_amount(self):
        """
        Compute the amounts of the line.
        """
        for line in self:
            price = line.price_unit
            taxes = line.tax_ids.compute_all(price, line.project_id.currency_id, line.product_qty, product=line.product_id, partner=line.project_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'line_total': taxes['total_included'],
                # 'subtotal': taxes['total_excluded'],
            })
                

    @api.depends('product_id', 'product_qty','price_unit','duration')
    def _compute_subtotal(self):
        for rec in self:
            subtotal = rec.product_qty * rec.price_unit * rec.duration
            rec.write({'subtotal': subtotal})

    @api.onchange('product_id', 'product_qty','price_unit','duration')
    def _onchange_subtotal(self):
        for rec in self:
            subtotal = rec.product_qty * rec.price_unit * rec.duration
            rec.write({'subtotal': subtotal})

    @api.model
    def create(self, vals):
        detail = super(Estimateline, self).create(vals)
        return detail

    def write(self, vals):
        res = super(Estimateline, self).write(vals)
        return res