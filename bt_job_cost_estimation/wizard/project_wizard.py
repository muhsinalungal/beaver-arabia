# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleProjectWizard(models.TransientModel):
    _name = 'sale.project.wizard'
    _description = 'Sale Project'

    project_template_id = fields.Many2one('project.project', 'Project Template')
    sale_project_id = fields.Many2one('sale.project', 'Sale Project')
    # project_template = fields.Boolean(string="Project Template",related='project_template_id.project_template',store=True)
    
    @api.model
    def default_get(self, fields):

       
        result = super(SaleProjectWizard, self).default_get(fields)

        if self.env.context.get('active_id'):
            result['sale_project_id'] = self.env.context.get('active_id')
        return result
    
    
    
    def new_project(self):
        for i in self:
            template=i.project_template_id
            stage_type_obj = self.env['project.task.type']
            state_template_id = stage_type_obj.search([('name', '=', 'Template')], limit=1)
            state_new_id = stage_type_obj.search([('name', '=', 'New')], limit=1)
            test = template.name
            project_id = template.copy()
            i.sale_project_id.project_ref_id=project_id
            if state_template_id:
                project_id.write({'stage_id':state_new_id.id, 'sequence_state':1})
            return project_id
