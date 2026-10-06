from odoo import api, fields, models
from odoo.exceptions import UserError

from .common import CONDITIONS, SURFACES, TEETH


class DentalTreatment(models.Model):
    _name = 'dental.treatment'
    _description = 'Dental Treatment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', default='New', readonly=True, copy=False)
    patient_id = fields.Many2one('dental.patient', required=True, tracking=True, index=True)
    dentist_id = fields.Many2one('dental.dentist', required=True, tracking=True)
    appointment_id = fields.Many2one('dental.appointment')
    date = fields.Date(default=fields.Date.context_today, required=True)
    state = fields.Selection([
        ('draft', 'Draft'), ('in_progress', 'In Progress'),
        ('done', 'Completed'), ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)
    diagnosis = fields.Text()
    notes = fields.Text(string='Clinical Notes')
    line_ids = fields.One2many('dental.treatment.line', 'treatment_id', copy=True)
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    amount_total = fields.Monetary(compute='_compute_amount', store=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True, copy=False)
    payment_state = fields.Selection(related='invoice_id.payment_state', string='Payment Status')
    chart_updated = fields.Boolean(copy=False)

    @api.depends('line_ids.subtotal')
    def _compute_amount(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('subtotal'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.treatment') or 'New'
        return super().create(vals_list)

    def action_start(self):
        self.state = 'in_progress'

    def action_done(self):
        Tooth = self.env['dental.tooth.line']
        for rec in self:
            rec.state = 'done'
            if not rec.chart_updated:
                for line in rec.line_ids.filtered(lambda l: l.tooth_number and l.new_condition):
                    Tooth.create({
                        'patient_id': rec.patient_id.id, 'tooth_number': line.tooth_number,
                        'surface': line.surface, 'condition': line.new_condition,
                        'dentist_id': rec.dentist_id.id, 'date': rec.date,
                        'notes': 'From treatment %s: %s' % (rec.name, line.procedure_id.name),
                    })
                rec.chart_updated = True
            if rec.appointment_id and rec.appointment_id.state in ('checked_in', 'in_progress'):
                rec.appointment_id.state = 'done'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_draft(self):
        self.state = 'draft'

    def action_create_invoice(self):
        self.ensure_one()
        if self.invoice_id:
            return self.action_view_invoice()
        if not self.line_ids:
            raise UserError("Add at least one procedure before creating an invoice.")
        lines = []
        for line in self.line_ids:
            label = line.procedure_id.name
            if line.tooth_number:
                label += ' (Tooth %s)' % line.tooth_number
            lines.append((0, 0, {
                'name': label, 'quantity': line.quantity,
                'price_unit': line.price_unit, 'discount': line.discount,
            }))
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.patient_id.partner_id.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_origin': self.name,
            'invoice_line_ids': lines,
        })
        self.invoice_id = move
        return self.action_view_invoice()

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'res_model': 'account.move',
            'res_id': self.invoice_id.id, 'view_mode': 'form',
        }


class DentalTreatmentLine(models.Model):
    _name = 'dental.treatment.line'
    _description = 'Treatment Line'

    treatment_id = fields.Many2one('dental.treatment', required=True, ondelete='cascade')
    patient_id = fields.Many2one(related='treatment_id.patient_id', store=True)
    date = fields.Date(related='treatment_id.date', store=True)
    procedure_id = fields.Many2one('dental.procedure', required=True)
    category = fields.Selection(related='procedure_id.category', store=True)
    tooth_number = fields.Selection(TEETH, string='Tooth')
    surface = fields.Selection(SURFACES)
    new_condition = fields.Selection(CONDITIONS, string='Chart Status After',
                                     help='If set, the dental chart is updated when the treatment is completed.')
    description = fields.Char()
    quantity = fields.Float(default=1.0)
    price_unit = fields.Monetary(compute='_compute_price', store=True, readonly=False)
    discount = fields.Float(string='Disc. %')
    currency_id = fields.Many2one(related='treatment_id.currency_id')
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True)

    @api.depends('procedure_id')
    def _compute_price(self):
        for line in self:
            line.price_unit = line.procedure_id.price

    @api.depends('quantity', 'price_unit', 'discount')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit * (1 - (line.discount or 0.0) / 100.0)
