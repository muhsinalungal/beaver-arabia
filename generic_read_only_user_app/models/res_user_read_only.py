# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools,_
from odoo.exceptions import ValidationError

class ResUser(models.Model):
    _inherit = 'res.users'

    read_only = fields.Boolean(string="Make Read Only")
    
    @api.onchange('read_only')
    def set_read_only_user(self):
        read_only_grp_id = self.env['ir.model.data'].get_object_reference('generic_read_only_user_app', 'group_read_only_user')[1]
        if not self.read_only:
            self.read_only = True
            group_list = []
            for group in self.groups_id:
                group_list.append(group.id)
            group_list.append(read_only_grp_id)
            result= self.write({'groups_id':([(6,0,group_list)])})
        
        elif self.read_only:
            self.read_only = False
            group_list2 = []
            for group in self.groups_id:
                if group.id != read_only_grp_id: 
                    group_list2.append(group.id)
            result= self.write({'groups_id':([(6,0,group_list2)])})

class IrModelAccess(models.Model):
    _inherit = 'ir.model.access'

    @api.model
    @tools.ormcache_context('self._uid', 'model', 'mode', 'raise_exception', keys=('lang',))
    def check(self, model, mode='read', raise_exception=True):
        result = super(IrModelAccess, self).check(model, mode, raise_exception=raise_exception)
        if self.env.user.has_group('generic_read_only_user_app.group_read_only_user') and model not in ['res.users.log','res.users','mail.channel','mail.alias',
                  'bus.presence','res.lang',
                  'aged.partner.balance.report.wizard','general.ledger.report.wizard'
                  ,'account.report.standard.ledger.periode','account.report.standard.ledger',
                  'account.report.standard.ledger.report',
                  'account.report.standard.ledger.report.object',
                  'account.report.standard.ledger.line','partner.ledger',
                'kit.account.tax.report',
            'account.print.journal',
            'journal.ledger.report.wizard',
            'trial.balance.report.wizard',
            'open.items.report.wizard',
            'vat.report.wizard',
            'wiz.account.asset.report',
            'dynamic.balance.sheet.report',
            'account.general.ledger',
            'account.day.book',
            'account.trial.balance',
            'account.partner.ledger',
            'account.partner.ageing',
            'account.cash.flow',
            # 'mis.report.instance',
            # 'mis.report.instance.period'
                  ]:
            if mode != 'read':
                return False
        return result

class IrRule(models.Model):
    _inherit = 'ir.rule'

    def _compute_domain(self, model_name, mode="read"):
        res = super(IrRule,self)._compute_domain(model_name, mode)
        obj_list=['res.users.log','res.users','mail.channel','mail.alias',
                  'bus.presence','res.lang',
                  'aged.partner.balance.report.wizard','general.ledger.report.wizard'
                  ,'account.report.standard.ledger.periode','account.report.standard.ledger',
                  'account.report.standard.ledger.report',
                  'account.report.standard.ledger.report.object',
                  'account.report.standard.ledger.line','partner.ledger',
                  'kit.account.tax.report',
                  'account.print.journal',
                  'journal.ledger.report.wizard',
                  'trial.balance.report.wizard',
                  'open.items.report.wizard',
                  'vat.report.wizard',
                  'wiz.account.asset.report',
                  'dynamic.balance.sheet.report',
                  'account.general.ledger',
                  'account.day.book',
                  'account.trial.balance',
                  'account.partner.ledger',
                  'account.partner.ageing',
                  'account.cash.flow',
                  # 'mis.report.instance',
                  # 'mis.report.instance.period'
                  ]
        if model_name not in obj_list:
            if self.env.user.has_group('generic_read_only_user_app.group_read_only_user'):
                if mode != 'read':
                    raise ValidationError(_('User can not done this operation..! (%s)') % self.env.user.name)
        return res
