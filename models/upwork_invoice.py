# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
import csv


class UpworkInvoice(models.Model):
    _name = 'upwork.invoice'
    _description = "Upwork Invoice"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Ref ID', required=True)
    date = fields.Char(string='Date')
    invoice_date = fields.Date(string='Date', compute='_compute_date', store=True)
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

    def convertDate(self, DateString):
        Datelist = DateString.split()
        month = Datelist[0]
        day = Datelist[1].strip(',')
        year = Datelist[2]
        DateConst = month + " " + day + " " + year
        DateResult = datetime.strptime(DateConst, '%b %d %Y').date()
        return DateResult

    @api.depends('date')
    def _compute_date(self):
        for record in self:
            record.invoice_date = self.convertDate(record.date)

    def _get_default_stage_id(self):
        return self.env['upwork.invoice.stage'].search([], order='sequence', limit=1)
    
    @api.model
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


class UpworkInvoiceImport(models.Model):
    _name = 'upwork.invoice.import'
    _description = "Upwork Invoice Import"
    
    invoice_files = fields.Many2many(comodel_name='ir.attachment', relation='class_ir_attachments_rel_upwork_invoice', column1='class_id', column2='attachment_id', string='Attachments')

    def convertDate(self, DateString):
        Datelist = DateString.split()
        month = Datelist[0]
        day = Datelist[1].strip(',')
        year = Datelist[2]
        DateConst = month + " " + day + " " + year
        DateResult = datetime.strptime(DateConst, '%b %d %Y').date()
        return DateResult
    
    def import_file(self, invoice_file):
        fileobj = TemporaryFile('wb+') 
        fileobj.write(base64.decodestring(invoice_file))
        fileobj.seek(0)
        str_csv_data = fileobj.read().decode('utf-8')
        lis = csv.reader(StringIO(str_csv_data), delimiter=',')
        rownum = 0
        faulty_rows = []
        header = ''
        cust_invoice_numbers = {}
        invocie_list = [] 

    def import_files(self):
        for record in self.invoice_files:
            self.import_file(record)
        
        return {'type': 'ir.actions.act_window_close'}