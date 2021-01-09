# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import csv


class UpworkInvoice(models.Model):
    _name = 'upwork.invoice'
    _description = "Upwork Invoice"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Ref ID', required=True)
    date = fields.Char(string='Date')
    invoice_date = fields.Date(string='Invoice date', compute='_compute_date', store=True)
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
    
    def import_file(self, invoice_file):
        filename = invoice_file.datas_fname
        with open(filename, 'r') as data:
            for line in csv.DictReader(data):
                if self.env['res.partner'].search([('name', '=', line['Agency'])]):
                    agency = self.env['res.partner'].search([('name', '=', line['Agency'])])
                else :
                    agency = self.env['res.partner'].create({'name': line['Agency']})
                
                if self.env['res.partner'].search([('name', '=', line['Freelancer'])]):
                    freelancer = self.env['res.partner'].search([('name', '=', line['Freelancer'])])
                else :
                    freelancer = self.env['res.partner'].create({'name': line['Freelancer']})
                
                self.env['upwork.invoice'].create({
                    'name': line['Ref ID'], 
                    'date': line['Date'] if 'Date' in line.keys() else '', 
                    'invoice_type': line['Type'] if 'Type' in line.keys() else '',
                    'description': line['Description'] if 'Description' in line.keys() else '',
                    'agency': agency,
                    'freelancer': freelancer,
                    'team': line['Team'] if 'Team' in line.keys() else '',
                    'account_name': line['Account Name'] if 'Account Name' in line.keys() else '',
                    'po': line['PO'] if 'PO' in line.keys() else '',
                    'amount': float(line['Amount']) if 'Amount' in line.keys() else None,
                    'amount_local_currency': float(line['Amount in local currency']) if 'Amount in local currency' in line.keys() else None,
                    'balance': float(line['Balance']) if 'Balance' in line.keys() else None,
                    'invoice_file': invoice_file,
                    })

    def import_files(self):
        for record in self.invoice_files:
            self.import_file(record)
        
        return {'type': 'ir.actions.act_window_close'}