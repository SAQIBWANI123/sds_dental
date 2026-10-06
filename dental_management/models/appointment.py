from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class DentalAppointment(models.Model):
    _name = 'dental.appointment'
    _description = 'Dental Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc'

    name = fields.Char(string='Reference', default='New', readonly=True, copy=False)
    patient_id = fields.Many2one('dental.patient', required=True, tracking=True, index=True)
    dentist_id = fields.Many2one('dental.dentist', required=True, tracking=True, index=True)
    room_id = fields.Many2one('dental.room', string='Room / Chair')
    start_datetime = fields.Datetime(string='Start', required=True, tracking=True,
                                     default=lambda s: fields.Datetime.now())
    duration = fields.Float(default=0.5, help='Duration in hours')
    end_datetime = fields.Datetime(string='End', compute='_compute_end', store=True)
    state = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('checked_in', 'Checked In'),
        ('in_progress', 'In Progress'), ('done', 'Done'),
        ('cancelled', 'Cancelled'), ('no_show', 'No Show'),
    ], default='draft', tracking=True, index=True)
    priority = fields.Selection([('0', 'Normal'), ('1', 'Urgent')], default='0')
    reason = fields.Char(string='Reason for Visit')
    procedure_ids = fields.Many2many('dental.procedure', string='Planned Procedures')
    notes = fields.Text()
    reminder_sent = fields.Boolean(copy=False)
    color = fields.Integer(related='dentist_id.color')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    treatment_ids = fields.One2many('dental.treatment', 'appointment_id')
    treatment_count = fields.Integer(compute='_compute_treatment_count')

    @api.depends('start_datetime', 'duration')
    def _compute_end(self):
        for rec in self:
            rec.end_datetime = (rec.start_datetime + timedelta(hours=rec.duration or 0.5)
                                if rec.start_datetime else False)

    def _compute_treatment_count(self):
        for rec in self:
            rec.treatment_count = len(rec.treatment_ids)

    @api.onchange('procedure_ids')
    def _onchange_procedure_ids(self):
        if self.procedure_ids:
            self.duration = max(sum(self.procedure_ids.mapped('duration')), 0.25)

    @api.constrains('start_datetime', 'duration', 'dentist_id', 'room_id', 'state')
    def _check_overlap(self):
        for rec in self:
            if rec.state in ('cancelled', 'no_show') or not rec.start_datetime:
                continue
            base = [('id', '!=', rec.id), ('state', 'not in', ('cancelled', 'no_show')),
                    ('start_datetime', '<', rec.end_datetime), ('end_datetime', '>', rec.start_datetime)]
            if self.search_count(base + [('dentist_id', '=', rec.dentist_id.id)]):
                raise ValidationError(
                    "Dr. %s already has an appointment during this time slot." % rec.dentist_id.name)
            if rec.room_id and self.search_count(base + [('room_id', '=', rec.room_id.id)]):
                raise ValidationError("Room %s is already booked during this time slot." % rec.room_id.name)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.appointment') or 'New'
        return super().create(vals_list)

    # workflow
    def action_confirm(self):
        template = self.env.ref('dental_management.mail_template_appointment_confirm',
                                raise_if_not_found=False)
        for rec in self:
            rec.state = 'confirmed'
            if template and rec.patient_id.email:
                template.send_mail(rec.id, force_send=False)

    def action_check_in(self):
        self.state = 'checked_in'

    def action_start(self):
        self.state = 'in_progress'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_no_show(self):
        self.state = 'no_show'

    def action_reset(self):
        self.state = 'draft'

    def action_create_treatment(self):
        self.ensure_one()
        lines = [(0, 0, {'procedure_id': p.id}) for p in self.procedure_ids]
        treatment = self.env['dental.treatment'].create({
            'patient_id': self.patient_id.id, 'dentist_id': self.dentist_id.id,
            'appointment_id': self.id, 'line_ids': lines,
        })
        return {
            'type': 'ir.actions.act_window', 'res_model': 'dental.treatment',
            'res_id': treatment.id, 'view_mode': 'form',
        }

    def action_view_treatments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': 'Treatments', 'res_model': 'dental.treatment',
            'view_mode': 'list,form', 'domain': [('appointment_id', '=', self.id)],
        }

    @api.model
    def _cron_send_reminders(self):
        template = self.env.ref('dental_management.mail_template_appointment_reminder',
                                raise_if_not_found=False)
        if not template:
            return
        now = fields.Datetime.now()
        appts = self.search([
            ('state', 'in', ('draft', 'confirmed')), ('reminder_sent', '=', False),
            ('start_datetime', '>=', now), ('start_datetime', '<=', now + timedelta(hours=24)),
        ])
        for appt in appts.filtered(lambda a: a.patient_id.email):
            template.send_mail(appt.id, force_send=False)
            appt.reminder_sent = True
