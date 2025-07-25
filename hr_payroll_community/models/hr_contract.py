# -*- coding:utf-8 -*-

from odoo import api, fields, models


class HrContract(models.Model):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure')
    schedule_pay = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi-annually', 'Semi-annually'),
        ('annually', 'Annually'),
        ('weekly', 'Weekly'),
        ('bi-weekly', 'Bi-weekly'),
        ('bi-monthly', 'Bi-monthly'),
    ], string='Scheduled Pay', index=True, default='monthly',
        help="Defines the frequency of the wage payment.")
    resource_calendar_id = fields.Many2one(required=True, help="Employee's working schedule.")
    hra = fields.Monetary(string='HRA', tracking=True, help="House rent allowance.")
    travel_allowance = fields.Monetary(string="Travel Allowance", help="Travel allowance")
    da = fields.Monetary(string="DA", help="Dearness allowance")
    meal_allowance = fields.Monetary(string="Food Allowance", help="Food allowance")
    medical_allowance = fields.Monetary(string="Medical Allowance", help="Medical allowance")
    other_allowance = fields.Monetary(string="Other Allowance", help="Other allowances")
    variable_allowance = fields.Monetary(string="Variable Allowance")
    fixed_allowance = fields.Monetary(string="Fixed Allowance")
    total_allowance = fields.Monetary(string="Total", compute="_compute_total_allowance", readonly=True)
    
    
    @api.depends('wage', 'hra', 'travel_allowance', 'da', 'meal_allowance', 'medical_allowance', 'other_allowance', 'variable_allowance', 'fixed_allowance')
    def _compute_total_allowance(self):
        for rec in self:
            allowances = 0.0
            if rec.wage:
                allowances += rec.wage
            if rec.hra:
                allowances += rec.hra
            if rec.travel_allowance:
                allowances += rec.travel_allowance
            if rec.da:
                allowances += rec.da
            if rec.meal_allowance:
                allowances += rec.meal_allowance
            if rec.medical_allowance:
                allowances += rec.medical_allowance
            if rec.other_allowance:
                allowances += rec.other_allowance
            if rec.variable_allowance:
                allowances += rec.variable_allowance
            if rec.fixed_allowance:
                allowances += rec.fixed_allowance
            rec.total_allowance = allowances
            
            
            
    def get_all_structures(self):

        """
        @return: the structures linked to the given contracts, ordered by hierachy (parent=False first,
                 then first level children and so on) and without duplicata
        """
        structures = self.mapped('struct_id')
        if not structures:
            return []
        # YTI TODO return browse records
        return list(set(structures._get_parent_structure().ids))

    def get_attribute(self, code, attribute):

        return self.env['hr.contract.advantage.template'].search([('code', '=', code)], limit=1)[attribute]

    def set_attribute_value(self, code, active):
        for contract in self:

            if active:

                value = self.env['hr.contract.advantage.template'].search([('code', '=', code)], limit=1).default_value
                contract[code] = value
            else:

                contract[code] = 0.0


class HrContractAdvandageTemplate(models.Model):
    _name = 'hr.contract.advantage.template'
    _description = "Employee's Advantage on Contract"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    lower_bound = fields.Float('Lower Bound', help="Lower bound authorized by the employer for this advantage")
    upper_bound = fields.Float('Upper Bound', help="Upper bound authorized by the employer for this advantage")
    default_value = fields.Float('Default value for this advantage')
