from odoo import models, fields, api


class SaleOrder(models.Model):

    _inherit = "sale.order"

    estimate_id = fields.Many2one('sale.estimate', "Sale Estimate")
    work_matrix_ids = fields.One2many('work.matrix.line','sale_order_id' )

    @api.onchange(estimate_id)
    def load_work_matrix(self):

        template_lines =[]
        if self.estimate_id:
            template_id = self.estimate_id.sale_template_id
            for rec in template_id.template_line_ids:
                template_lines.append((0,0,{'name':rec.name, 'contractor': rec.contractor, 'gambit':rec.gambit, 'sequence':rec.sequence, 'sale_order_id':self.id}))
            self.write({'work_matrix_ids':template_lines})
