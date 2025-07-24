from datetime import datetime, timedelta
import pytz
import os
import csv
import tempfile
from dateutil.relativedelta import relativedelta
import dateutil.relativedelta
import base64
import dateutil.rrule as rrule
import io
import xlrd
import calendar
import dateutil.parser
import math

from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from openerp.exceptions import UserError, Warning 
from openerp import tools as openerp_tools

class import_estimate(models.TransientModel):
    _name = 'import.estimate'
    
    
    @api.model
    def default_get(self, fields):
        result = super(import_estimate, self).default_get(fields)

        if self.env.context.get('project_id'):
            result['project_id'] = self.env.context.get('project_id')
        return result

    import_file = fields.Binary('File')
    file_name = fields.Char('File Name')
    project_id = fields.Many2one('sale.project',string='Project')
    
    
    def import_data(self):
        try:
            file = str(base64.decodestring(self.import_file).decode('utf-8'))
            
            myreader = csv.reader(file.splitlines())
            split_header = True  
            skip_header=True
            running_tmpl = None  
            count_create = 0
            project_id=self.project_id.id
            for row in myreader:
                estimate_vals={}
                if split_header:
                    split_header=False
                    continue 
                else: 
                    description = row[0]
                    reference_number=row[1]
                    note = row[2]
                    uom=row[3]
                    work_quantity=row[4]
                    sale_margin=row[5]
                    
                    uom = self.env['uom.uom'].search([('name','=',uom)])
                    if uom:
                        estimate_vals.update({
                            'work_uom_id': uom[0].id
                })
                    estimate_ids = self.env['sale.estimate'].search([('name','=',description),('project_id','=',project_id)]) 
                    if not estimate_ids:
                        estimate_vals.update({
                            'name': description,
                            'reference_number':reference_number,
                            'note': note,
                            'work_quantity': work_quantity,
                            'project_id':project_id,
                            #'work_uom_id': supplier,
                            #'subtotal': is_sub_contractor,
                            #'amount_total': construction_partner_type,
                            #'cost_per_unit_work': import_data.get('Phone'),
                            'sale_margin':sale_margin
                            
                        })
                        estimate_obj = self.env['sale.estimate'].create(estimate_vals)
        except Exception as e:
            raise UserError(_('Please select the file in correct format.'))     
        
        return True           
        
class import_estimate_line(models.TransientModel):
    _name = 'import.estimate.line'

    @api.model
    def default_get(self, fields):
        result = super(import_estimate_line, self).default_get(fields)

        if self.env.context.get('project_id'):
           
            result['project_id'] = self.env.context.get('project_id')
        return result

    import_file = fields.Binary('File')
    file_name = fields.Char('File Name')
    project_id = fields.Many2one('sale.project',string='Project')
    
    
    
    def import_data(self):
        try:
            file = str(base64.decodestring(self.import_file).decode('utf-8'))
            myreader = csv.reader(file.splitlines())
            split_header = True  
            skip_header=True
            running_tmpl = None  
            count_create = 0 
            project_id=self.project_id.id  
            estimate_line_vals={}
            for row in myreader:
                estimate_line_vals.update({
                            'project_id':'',
                            'name':'',
                            'product_id':'',
                            'product_description':'',
                            'product_qty': '',
                            'product_uom_id':'',
                            'price_unit':''})
                if split_header:
                    split_header=False
                    continue 
                else: 
                    
                    estimate=row[0]
                    estimate_ids = self.env['sale.estimate'].search([('reference_number','=',estimate),('project_id','=',project_id)])
                    if estimate_ids:
                        estimate_line_vals.update({
                            'estimate_id': estimate_ids[0].id
                            })
                    else:
                        estimate_line_vals.update({
                            'estimate_id': '',
                            })
                    product=row[1]
                    product_qty = row[2]
                    
                    product = self.env['product.product'].search([('name','=',product)])
                    project = self.env['sale.project'].search([('id','=',project_id)])
                    if product:
                        estimate_line_vals.update({
                            'product_id': product[0].id,
                            'name':product.name,
                            'description': product.name,
                        })
                        
                        
                        
                    estimate_line_vals.update({
                        'project_id':project_id,
                        'product_qty': product_qty,
                        
                    })
                    estimate_line_ids=None
                    if estimate_ids and project_id and product.name :
                        estimate_ref=estimate_ids[0].id
                        estimate_line_ids = self.env['sale.estimate.line'].search([('estimate_id','=',estimate_ref),('project_id','=',project_id),('name','=',product.name)])
                        estimate_line_ids.product_id_change()
                    if not estimate_line_ids:
                        estimate_line_obj = self.env['sale.estimate.line'].create(estimate_line_vals) 
                        estimate_line_obj.product_id_change()
        except Exception as e:
            raise UserError(_('Please select the file in correct format.'))                
        return True  


class import_detail_estimate_line(models.TransientModel):
    _name = 'import.detail.estimate.line'

    @api.model
    def default_get(self, fields):
        result = super(import_detail_estimate_line, self).default_get(fields)

        if self.env.context.get('project_id'):
            result['project_id'] = self.env.context.get('project_id')
        return result

    import_file = fields.Binary('File')
    file_name = fields.Char('File Name')
    project_id = fields.Many2one('sale.project',string='Project')
    
    
    
    def import_data(self):
        try:
            file = str(base64.decodestring(self.import_file).decode('utf-8'))
            myreader = csv.reader(file.splitlines())
            split_header = True  
            skip_header=True
            running_tmpl = None  
            count_create = 0 
            project_id=self.project_id.id  
            estimate_line_vals={}
            for row in myreader:
                estimate_line_vals.update({
                            'project_id':'',
                            'estimate_id':'',
                            'name':'',
                            'number':'',
                            'length1':'',
                            'width':'',
                            'height': '',
                            'coefficient':'',
                            'remarks':''})
                if split_header:
                    split_header=False
                    continue 
                else: 

                    
                    estimate=row[0]
                    estimate_ids = self.env['sale.estimate'].search([('reference_number','=',estimate),('project_id','=',project_id)])
                    if estimate_ids:
                        estimate_line_vals.update({
                            'estimate_id': estimate_ids[0].id,
                            'uom_id' : estimate_ids.work_uom_id.id,
                            })
                    else:
                        estimate_line_vals.update({
                            'estimate_id': '',
                            'uom_id': '',
                            })


                    name=row[1]
                    number = row[2]
                    length = row[3]
                    width=row[4]
                    height=row[5]
                    coefficient = row[6]
                    remarks = row[7]
                    
                  
                    estimate_line_vals.update({
                        'project_id':project_id,
                        'name':name,
                        'number': number,
                        'length1': length,
                        'width':width,
                        'height':height,
                        'coefficient':coefficient,
                        'remarks':remarks,
                        
                        
                    })
                    print ('estimate_line_vals_____',estimate_line_vals)
                    estimate_line_ids=None
                    if estimate_ids and project_id and name :
                        estimate_ref=estimate_ids[0].id
                        estimate_line_ids = self.env['sale.estimate.details'].search([('estimate_id','=',estimate_ref),('project_id','=',project_id),('name','=',name)])
                        if estimate_line_ids:
                            estimate_line_ids._onchange_values()
                    if not estimate_line_ids:

                        estimate_line_obj = self.env['sale.estimate.details'].create(estimate_line_vals) 
                        estimate_line_obj._onchange_values()
                        
        except Exception as e:
            raise UserError(_('Please select the file in correct format.'))                
        return True                    



class import_wizard(models.TransientModel):
    _name = 'import.wizard'

    @api.model
    def default_get(self, fields):
        result = super(import_wizard, self).default_get(fields)

        if self.env.context.get('active_id'):
            result['project_id'] = self.env.context.get('active_id')
        return result
    


    import_option = fields.Selection([
        ('estimate', 'Import Estimate'),
        ('rate_analysis', 'Import Rate Analysis'),
        ('detail_estimate', 'Import Details Estimates'),
        ],
        default='estimate',
    )

    project_id = fields.Many2one('sale.project',string='Project')
