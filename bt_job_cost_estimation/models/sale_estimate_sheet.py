# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta



class SummaryWork(models.Model):
    _name = 'summary.work'
  
    sale_project_id = fields.Many2one('estimate.sheet',string='Sale Project Ref.')
    name = fields.Char(string="Description",)
    duration = fields.Float(string="Duration",)
    product_id = fields.Many2one(
        'product.product',
        string='Product',

    )


class Projects(models.Model):
    _name = "estimate.sheet"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Construction Cost Estimate "
    _rec_name = 'name'

    number = fields.Char(
        'Number',
        copy=True,
    )
    name = fields.Char('Number', copy=True, default=lambda self: _('New'))

    description = fields.Char("Description")
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
        related='estimate_id.state'
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
        string='Customer Reference'
    )
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
        store=True,
    )
    user_id = fields.Many2one(
        'res.users',
        'Sales Person',
        default=lambda self: self.env.user,
    )
    estimate_id = fields.Many2one(
        'sale.estimate',
        'Estimate',
       
    )
   
    estimate_line_ids = fields.One2many('sale.estimate.line','project_id','Wages Estimate Line',
                                            domain=[('estimate_type','=','wages')],store=True,copy=True)
    equip_estimate_line_ids = fields.One2many('sale.estimate.line','project_id','Equipment Estimate Line',
                                            domain=[('estimate_type','=','equipment')],store=True,copy=True)
    material_estimate_line_ids = fields.One2many('sale.estimate.line','project_id','Material Estimate Line',
                                            domain=[('estimate_type','=','material')],store=True,copy=True)
    general_estimate_line_ids = fields.One2many('sale.estimate.line','project_id','General Estimate Line',
                                            domain=[('estimate_type','=','general')],store=True,copy=True)

    
    total_amount = fields.Float(
        string="Amount Total",
        
        default=0.0
    )

    total = fields.Float(
        string="Total",
        compute='_compute_amount',
        default=0.0
    )
    dia_measure_id = fields.Many2one('diameter.measure',string='DIA Measure')
    project_ref_id = fields.Many2one('project.project',string='Project Ref.')
    email_from = fields.Char('Email', tracking=40, index=True,compute='_compute_email_from',readonly=False, store=True)
    phone = fields.Char('Phone', tracking=50,compute='_compute_phone', readonly=False, store=True)

    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string='Fiscal Position',
        domain="[('company_id', '=', company_id)]", check_company=True)
    
    version_number = fields.Float(
        string="Version Number",default=0.0)
    parent_version_id = fields.Many2one(
        'estimate.sheet',
        string='Parent Version',
        )
    parent_version_name = fields.Char('parent_version_name')
    child_version_number = fields.Float(
        string="Child Version Number",default=0.0)
    project_count = fields.Integer('# Estimates', compute='_compute_project_count')
    division_id = fields.Many2one(
        comodel_name="site.site",
        string="Division",)
    rfq_ref = fields.Char(string="RFQ Ref",readonly=True)
    contact_no = fields.Char(string="Contract No",)
    tender_no = fields.Char(string="Tender No",)
    job_desc = fields.Char(string="Job Description",)
    diameter = fields.Char(string="Diameter",)
    wall_thickness = fields.Char(string="Wall Thickness",)
    soil_condition = fields.Char(string="Soil Condition",)
    no_of_crossing = fields.Integer(string="No Of Crossing",)
    borring_length = fields.Float(string="Borring Length",)
    borring_depth = fields.Float(string="Borring Depth",)
    avg_length = fields.Float(string="Average Length",)
    method_choosen = fields.Char(string="Method Choosen",)

    carrier_pipe_dia = fields.Char(string="Carrier Pipe Dia",)
    summary_work_ids = fields.One2many('summary.work','sale_project_id','Summary Works',copy=True)
    total_planning = fields.Float(string="Average Depth",compute='compute_total_planning',store=True)
    project_duration = fields.Float(string="Project Duration",)
    microtunneling_setup = fields.Float(string="Microtunneling Setup",)
    duration_micro = fields.Float(string="Project Duration/Microtunneling Setup",)
    total_wages = fields.Float(
        string="Total Wages",
        compute='_compute_wages',
        default=0.0,store=True
    )
    wages_markup = fields.Float(
        string="Markup",
        default=0.0,
    )
    wages_sale = fields.Float(
        string="Sale",
        default=0.0,
    )

    total_equipment = fields.Float(
        string="Total Equipment",
        compute='_compute_equip',
        default=0.0,store=True
    )
    equipment_markup = fields.Float(
        string="Markup",
        default=0.0,
    )
    equipment_sale = fields.Float(
        string="Sale",
        default=0.0,
    )
    total_general = fields.Float(
        string="Total General",
        compute='_compute_general',
        default=0.0,store=True
    )
    general_markup = fields.Float(
        string="Markup",
        default=0.0,
    )
    general_sale = fields.Float(
        string="Sale",
        default=0.0,
    )
    total_material = fields.Float(
        string="Total Materials",
        compute='_compute_material',
        default=0.0,store=True
    )
    material_markup = fields.Float(
        string="Markup",
        default=0.0,
    )
    material_sale = fields.Float(
        string="Sale",
        default=0.0,
    )
    total_cost = fields.Float(
        string="Total Cost",
        compute='_compute_total_cost',
        store=True
    )
    total_sale = fields.Float(
        string="Total Sale",
        compute='_compute_total_sale',
        store=True
    )
    contigency_rate = fields.Float(
        string="Contigency Rate",
       
    )
    contigency = fields.Float(
        string="Contigency 10%",
        compute='_compute_total_cost',
        store=True
    )
    final_markup = fields.Float(
        string="Final Total With Mark Up",
        compute='_compute_final_markup',
        store=True
    )
    project_cost = fields.Float(
        string="Project Cost",
        compute='_compute_final_markup',
        store=True
    )
    project_po_value =fields.Float(
        string="Project PO Value",
        
    )
    profit =fields.Float(
        string="Profit",
        compute='_compute_profit',
        store=True    
    )
    markup = fields.Float(
        string="Markup",
        compute='_compute_profit',
        store=True    
    )
    total_meter =fields.Float(
        string="Total Meter",related='borring_length',
        
    )
    
    rate_lm = fields.Float(
        string="Rate/LM",compute='_compute_rate_lm',
        
    )
    total_contract_amt = fields.Float(
        string="Total Contract Amount",compute='_compute_contract_amt',
        
    )
    bid = fields.Float(
        string="Bid",compute='_compute_rate_lm',
        
    )
    bid_rate = fields.Float(
        string="Bid Rate",
        
    )
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('project.estimate.seq.job') or _('New')
        return super(Projects, self).create(vals)

    @api.onchange('bid_rate')
    def onchange_bid_rate(self):
        if self.total_meter > 0.00: 
            total_amount = self.final_markup / self.total_meter
            if self.bid_rate > 0.00:
                bid = total_amount / self.bid_rate
            else:
                bid = 0.00
            self.write({'bid': bid})
        else:
            self.write({'bid': 0.00})
    @api.onchange('duration_micro')
    def onchange_duration_micro_line(self):
        if self.duration_micro:
            for wage in self.estimate_line_ids:
                if wage.duration > 0.00:
                    wage.duration = self.duration_micro
                    subtotal = wage.product_qty * wage.price_unit * wage.duration
                    wage.subtotal = subtotal
            for equip in self.equip_estimate_line_ids:
                if equip.duration > 0.00:
                    equip.duration = self.duration_micro
                    subtotal = equip.product_qty * equip.price_unit * equip.duration
                    equip.subtotal = subtotal
            for material in self.material_estimate_line_ids:
                if material.duration > 0.00:
                    material.duration = self.duration_micro
                    subtotal = material.product_qty * material.price_unit * material.duration
                    material.subtotal = subtotal
            for general in self.general_estimate_line_ids:
                if general.duration > 0.00:
                    general.duration = self.duration_micro
                    subtotal = general.product_qty * general.price_unit * general.duration
                    general.subtotal = subtotal

    @api.depends('rate_lm','total_meter',)
    def _compute_contract_amt(self):
        for rec in self:
            total_amount = rec.rate_lm * rec.total_meter
            rec.write({'total_contract_amt': total_amount})

    @api.depends('total_meter','final_markup',)
    def _compute_rate_lm(self):
        for rec in self:
            if rec.total_meter > 0.00: 
                total_amount = rec.final_markup / rec.total_meter
                if rec.bid_rate > 0.00:
                    bid = total_amount / rec.bid_rate
                else:
                    bid = 0.00
                rec.write({'rate_lm': total_amount,'bid': bid})
            else:
                rec.write({'rate_lm': 0.00,'bid': 0.00})

    @api.depends('total_wages','total_equipment','total_general','total_material','contigency_rate')
    def _compute_total_cost(self):
        for rec in self:
            total_amount = rec.total_wages + rec.total_equipment + rec.total_general + rec.total_material
            contigency = total_amount * (rec.contigency_rate/100)
            rec.write({'total_cost': total_amount,'contigency': contigency})

    @api.depends('wages_sale','equipment_sale','general_sale','material_sale')
    def _compute_total_sale(self):
        for rec in self:
            total_amount = rec.wages_sale + rec.equipment_sale + rec.general_sale + rec.material_sale
            rec.write({'total_sale': total_amount})

    @api.depends('total_sale','contigency')
    def _compute_final_markup(self):
        for rec in self:
            total_amount = rec.total_sale + rec.contigency
            rec.write({'final_markup': total_amount,'project_cost': total_amount})

    @api.depends('project_cost','project_po_value','final_markup','total_cost')
    def _compute_profit(self):
        for rec in self:
            total_amount = rec.project_po_value - rec.project_cost
            markup = rec.final_markup - rec.total_cost
            rec.write({'profit': total_amount,'markup': markup})


    @api.onchange('total_wages','wages_markup','estimate_line_ids.subtotal')
    def _onchange_wages_sale(self):
        if self.total_wages and self.wages_markup:
            perc = 1+(self.wages_markup/100)
            self.wages_sale = self.total_wages*perc
        elif self.total_wages == 0.00:
            self.wages_sale == 0.00

    @api.onchange('total_equipment','equipment_markup')
    def _onchange_equipment_sale(self):
        if self.total_equipment and self.equipment_markup:
            perc = 1+(self.equipment_markup/100)
            self.equipment_sale = self.total_equipment*perc

    @api.onchange('total_general','general_markup')
    def _onchange_general_sale_markup(self):
        if self.total_general and self.general_markup:
            perc = 1+(self.general_markup/100)
            self.general_sale = self.total_general*perc

    @api.onchange('total_material','material_markup')
    def _onchange_material_sale(self):
        if self.total_material and self.material_markup:
            perc = 1+(self.material_markup/100)
            self.material_sale = self.total_material*perc


    @api.onchange('borring_length','no_of_crossing')
    def _onchange_avg_length(self):
        if self.borring_length and self.no_of_crossing:
            self.avg_length = self.borring_length/self.no_of_crossing

    @api.onchange('total_planning','no_of_crossing')
    def _onchange_project_duration(self):
        if self.total_planning and self.no_of_crossing:
            self.project_duration = self.total_planning*self.no_of_crossing

    @api.onchange('microtunneling_setup','project_duration')
    def _onchange_duration_micro(self):
        if self.microtunneling_setup and self.project_duration:
            self.duration_micro = self.project_duration/self.microtunneling_setup

    @api.depends('summary_work_ids.duration')
    def compute_total_planning(self):
        for rec in self:
            total_amount = 0.0
            for line in self.summary_work_ids:
                total_amount += line.duration
            rec.write({'total_planning': total_amount})

    @api.depends('equip_estimate_line_ids.subtotal')
    def _compute_equip(self):
        for rec in self:
            total_amount = 0.0
            perc = 0.0
            for line in rec.equip_estimate_line_ids:
                if line.estimate_type == 'equipment':
                    total_amount += line.subtotal
                if rec.equipment_markup > 0.00:
                    perc = 1+(rec.equipment_markup/100)
                else:
                    perc = 0.00
                rec.write({'total_equipment': total_amount,'equipment_sale':total_amount*perc})

    @api.depends('estimate_line_ids.subtotal')
    def _compute_wages(self):
        for rec in self:
            total_amount = 0.0
            perc = 0.0
            for line in rec.estimate_line_ids:
                if line.estimate_type == 'wages':
                    total_amount += line.subtotal
                if rec.wages_markup > 0.00:
                    perc = 1+(rec.wages_markup/100)
                    # self.wages_sale = total_amount*perc
                else:
                    perc = 0.00
            rec.write({'total_wages': total_amount,'wages_sale':total_amount*perc})

    @api.depends('material_estimate_line_ids.subtotal')
    def _compute_material(self):
        for rec in self:
            total_amount = 0.0
            perc = 0.0
            for line in rec.material_estimate_line_ids:
                if line.estimate_type == 'material':
                    total_amount += line.subtotal
                if rec.material_markup > 0.00:
                    perc = 1+(rec.material_markup/100)
                else:
                    perc = 0.00
            rec.write({'total_material': total_amount,'material_sale':total_amount*perc})
    @api.depends('general_estimate_line_ids.subtotal')
    def _compute_general(self):
        for rec in self:
            total_amount = 0.0
            perc = 0.0
            for line in rec.general_estimate_line_ids:
                if line.estimate_type == 'general':
                    total_amount += line.subtotal
                if rec.general_markup > 0.00:
                    perc = 1+(rec.general_markup/100)
                else:
                    perc = 0.00
            rec.write({'total_general': total_amount,'general_sale':total_amount*perc})


    @api.depends('estimate_ids.discount')
    def _compute_discount(self):
        for rec in self:
            discount = 0.0
            for line in rec.estimate_ids:
                discount += line.discount
            rec.write({'discount': discount})

    @api.onchange('total_amount', 'discount')
    def _compute_amount(self):
        for rec in self:
            rec.total = rec.total_amount + rec.discount

    def _compute_project_count(self):
        for rec in self:
            estimate_lines = self.env['project.project'].search([('sale_project_id', "=", rec.id)])
            rec.write({'project_count': len(estimate_lines)})

    @api.depends('estimate_ids')
    def get_estimate_count(self):
        self.estimate_count = len(self.estimate_ids)

    @api.depends('partner_id.email')
    def _compute_email_from(self):
        for proj in self:
            if proj.partner_id.email and proj.partner_id.email != proj.email_from:
                proj.email_from = proj.partner_id.email

    @api.depends('partner_id.phone')
    def _compute_phone(self):
        for proj in self:
            if proj.partner_id.phone and proj.phone != proj.partner_id.phone:
                proj.phone = proj.partner_id.phone

    def get_estimate_line_count(self):
        for rec in self:
            estimate_lines = self.env['sale.estimate.line'].search([('project_id', "=", rec.id)])
            rec.write({'estimate_line_count': len(estimate_lines)})



    def sale_project_actions(self):
        action = self.env["ir.actions.actions"]._for_xml_id("project.open_view_project_all_config")
        action['context'] = {
            'default_sale_project_id': self.id,
            'default_partner_id': self.partner_id.id,
           
        }
        action['domain'] = [('id', '=', self.project_ref_id.id)]
        
       
        return action 

    def action_view_estimates(self):
        estimates = self.mapped('estimate_ids')
        action = self.env['ir.actions.act_window']._for_xml_id('bt_job_cost_estimation.action_estimate_job_cost')
        action['context'] = {'default_project_id': self.id, 'default_currency_id': self.currency_id.id}
        action['domain'] = [('id', 'in', estimates.ids)]
        return action

    def action_view_estimate_lines(self):
        estimates = self.env['sale.estimate.line'].search([('project_id', "=", self.id)])
        action = self.env['ir.actions.act_window']._for_xml_id('bt_job_cost_estimation.action_estimate_line')
        action['context'] = {'default_project_id': self.id, 'default_currency_id': self.currency_id.id, 'group_by': 'estimate_id'}
        action['domain'] = [('id', 'in', estimates.ids)]
        return action


    def estimate_send(self):
        for rec in self:
            rec.state = 'sent'

    def estimate_confirm(self):
        for rec in self:
            if rec.estimate_line_ids:
                for line in rec.estimate_line_ids:
                    if line.pricelist_active!=True:
                        raise UserError(_('Please Update the Product Price.'))
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


    def update_pricelist(self):
        for rec in self:
            if rec.estimate_line_ids:
                for line in rec.estimate_line_ids:
                    if line.product_uom_id and line.product_id and line.pricelist_id:
                        price = line.pricelist_id.get_product_price(product=line.product_id, quantity=line.product_qty or 1.0, partner=False,date=datetime.today(),uom_id=line.product_uom_id.id)
                        price_unit = line.product_id.uom_id._compute_price(price, line.product_uom_id)
                        if price_unit == 0.00:
                            pricelist_active=False
                        else:
                            pricelist_active=True
                      
                        self.env.cr.execute(
                                """
                            SELECT
                                item.id
                            FROM
                                product_pricelist_item AS item
                            WHERE
                                     (item.product_tmpl_id IS NULL OR item.product_tmpl_id = %s)
                            AND     (item.pricelist_id = %s)
                            AND     (item.date_start IS NULL OR item.date_start<=%s)
                            AND     (item.date_end IS NULL OR item.date_end>=%s)
                            """,
                            (line.product_id.product_tmpl_id.id,line.pricelist_id.id, datetime.today(), datetime.today()))
                        item_ids = [x[0] for x in self.env.cr.fetchall()] 
                        items=self.env['product.pricelist.item'].browse(item_ids)
                        active_check=0
                        if items:
                            for rule in items:
                                if price_unit == line.product_id.uom_id._compute_price(rule.fixed_price, line.product_uom_id):
                                    active_check=1    
                        if active_check == 1:
                            pricelist_active=True
                        else:
                            pricelist_active=False
                        line.write({'price_list_price': price_unit,'price_unit':price_unit,'pricelist_active':pricelist_active})
                    else:
                        line.price_unit=0.00
    
    
    
    # def estimate_to_quotation(self):
    #     return

    # def contract_close(self):
    #     return
    #
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


class DiameterMeasure(models.Model):
    _name = 'diameter.measure'

    name = fields.Char(string="Name",)
    desc = fields.Char(string="Description",)