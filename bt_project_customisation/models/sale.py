from odoo import models, fields,exceptions, api, _
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from datetime import date


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_project_vals(self,project_name):
        self.ensure_one()
        name = u" %s - %s - %s" % (
            self.partner_id.name,
            date.today().year,
            self.name)
        parent = self.env['stock.location'].search([('name', '=', 'My Co')],limit=1)
        if parent:
            warehouse_location = self.env['stock.location'].create({
            'name': project_name,
            'location_id':parent.id,
            'usage':'internal',
            'is_project_location':True,}).id
        else:
            warehouse_location = False
            
        return {
            'user_id': self.user_id.id,
            'name': project_name,
            'partner_id': self.partner_id.id,
            'site_location_id':warehouse_location,
            'estimate_sheet_id':self.estimate_sheet_id.id
        }

    def action_create_project(self,project_name):
        project_obj = self.env['project.project']
        for order in self:
            if order.project_id:
                raise exceptions.UserError(_(
                    'There is a project already related with this sale order.'
                ))
            vals = order._prepare_project_vals(project_name)
            project = project_obj.create(vals)
            order.write({
                'project_id': project.id or False
            })
        return True


class ProductTemplate(models.Model):
    _inherit = "product.template"

    forcast_type = fields.Selection([
        ('wages', 'Manpower'),
        ('equipment', 'Equipments'),
        ('material', 'Materials'),
        ('tools', 'Consumable and Tools'),
        ('accomodation', 'Accomodation'),
        ('spare', 'Spare part / Machinery Import'),
        ('inspection', 'Third Party Inspection'),
        ('tech_visit', 'Technician Visit'),
        ('vehicle', 'Hire Vehicle'),
        ('transport', 'Transport - Trailer Hire'),
        ('Repair', 'Repair & Maintenance'),
        ('travel', 'Travel Expense'),
        ('Consultancy', 'Consultancy Services'),
        ('safety', 'Safety Items / PPE Expenses'),
        ('misc', 'Miscellaneous Expense'),
        
       ],
        
        track_visibility='onchange',
        copy='True',
    )