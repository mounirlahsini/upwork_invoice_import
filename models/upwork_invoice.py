# -*- coding: utf-8 -*-

from odoo import models, fields, api


class UpworkInvoice(models.Model):
    _name = 'upwork.invoice'
    _description = "Upwork Invoice"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Ref ID', required=True)
    invoice_date = fields.Date(string='Date')
    invoice_type = fields.Selection(string="Type", selection=[('processing_fee', 'Processing Fee'), ('payment', 'Payment'), ('hourly', 'Hourly')])
    description = fields.Char(string='Description')
    agency = fields.Many2one('res.partner', string='Agency')
    freelancer = fields.Many2one('res.partner', string='Freelancer')

    team = fields.Char(string='Team')
    account_name = fields.Char(string='Account name')
    po = fields.Char(string='PO')

    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    amount_local_currency = fields.Monetary(string='Amount in local currency', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string="Currency", default= lambda self : self.env.ref('base.main_company').currency_id, readonly=True)
    balance = fields.Monetary(string='Balance', currency_field='currency_id')
    invoice_file = fields.Binary(string="Document")

    stage_id = fields.Many2one('upwork.invoice.stage', string='Stage', index=True, default=lambda s: s._get_default_stage_id(), group_expand='_read_group_stage_ids', track_visibility='onchange')
    in_progress = fields.Boolean(related='stage_id.in_progress')
    color = fields.Integer()

    def _get_default_stage_id(self):
        return self.env['upwork.invoice.stage'].search([], order='sequence', limit=1)
    
    #@api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return stages.sudo().search([], order=order)


class UpworkInvoiceStage(models.Model):
    _name = 'upwork.invoice.stage'
    _description = "Upwork Invoice Stage"
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True)
    description = fields.Text()
    sequence = fields.Integer(default=1)
    in_progress = fields.Boolean(string='In Progress', default=True)
    fold = fields.Boolean(string='Folded in Kanban', help='This stage is folded in the kanban view when there are not records in that stage to display.')