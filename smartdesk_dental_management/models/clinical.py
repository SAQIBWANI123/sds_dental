from odoo import api, fields, models

from .common import CONDITIONS, SURFACES, TEETH


class DentalToothLine(models.Model):
    _name = 'dental.tooth.line'
    _description = 'Dental Chart Entry'
    _order = 'date desc, id desc'

    patient_id = fields.Many2one('dental.patient', required=True, ondelete='cascade', index=True)
    tooth_number = fields.Selection(TEETH, string='Tooth', required=True)
    surface = fields.Selection(SURFACES, default='w')
    condition = fields.Selection(CONDITIONS, required=True, default='caries')
    date = fields.Date(default=fields.Date.context_today)
    dentist_id = fields.Many2one('dental.dentist')
    notes = fields.Char()


class DentalXray(models.Model):
    _name = 'dental.xray'
    _description = 'X-Ray / Clinical Image'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(required=True)
    patient_id = fields.Many2one('dental.patient', required=True, ondelete='cascade')
    dentist_id = fields.Many2one('dental.dentist')
    date = fields.Date(default=fields.Date.context_today)
    xray_type = fields.Selection([
        ('periapical', 'Periapical'), ('bitewing', 'Bitewing'), ('panoramic', 'Panoramic (OPG)'),
        ('cephalometric', 'Cephalometric'), ('cbct', 'CBCT'), ('photo', 'Intra-oral Photo'),
        ('other', 'Other')], default='periapical', string='Type')
    tooth_number = fields.Selection(TEETH, string='Tooth')
    image = fields.Image(max_width=1920, max_height=1920)
    notes = fields.Text(string='Findings')


class DentalLabOrder(models.Model):
    _name = 'dental.lab.order'
    _description = 'Dental Lab Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Reference', default='New', readonly=True, copy=False)
    patient_id = fields.Many2one('dental.patient', required=True, tracking=True)
    dentist_id = fields.Many2one('dental.dentist', required=True)
    lab_id = fields.Many2one('res.partner', string='Dental Lab')
    work_type = fields.Selection([
        ('crown', 'Crown'), ('bridge', 'Bridge'), ('denture', 'Denture'), ('implant', 'Implant Abutment'),
        ('veneer', 'Veneer'), ('aligner', 'Aligner / Retainer'), ('night_guard', 'Night Guard'),
        ('other', 'Other')], default='crown', required=True)
    tooth_number = fields.Selection(TEETH, string='Tooth')
    shade = fields.Char(help='e.g. A2')
    sent_date = fields.Date()
    due_date = fields.Date(tracking=True)
    received_date = fields.Date()
    state = fields.Selection([
        ('draft', 'Draft'), ('sent', 'Sent to Lab'), ('received', 'Received'),
        ('fitted', 'Fitted'), ('cancelled', 'Cancelled')], default='draft', tracking=True)
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    cost = fields.Monetary()
    notes = fields.Text(string='Instructions')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.lab.order') or 'New'
        return super().create(vals_list)

    def action_send(self):
        self.write({'state': 'sent', 'sent_date': fields.Date.context_today(self)})

    def action_receive(self):
        self.write({'state': 'received', 'received_date': fields.Date.context_today(self)})

    def action_fit(self):
        self.state = 'fitted'

    def action_cancel(self):
        self.state = 'cancelled'
