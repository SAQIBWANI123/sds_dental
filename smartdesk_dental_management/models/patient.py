from datetime import date

from odoo import api, fields, models

from .common import CONDITION_COLORS, GENDERS


class DentalPatient(models.Model):
    _name = 'dental.patient'
    _description = 'Dental Patient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(string='Patient ID', default='New', readonly=True, copy=False)
    partner_id = fields.Many2one('res.partner', string='Contact', ondelete='restrict', copy=False)
    image_1920 = fields.Image(max_width=1920, max_height=1920)
    image_128 = fields.Image(related='image_1920', max_width=128, max_height=128, store=True)
    birth_date = fields.Date(tracking=True)
    age = fields.Integer(compute='_compute_age')
    gender = fields.Selection(GENDERS, tracking=True)
    blood_group = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'), ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'), ('o+', 'O+'), ('o-', 'O-')])
    phone = fields.Char()
    email = fields.Char()
    street = fields.Char()
    city = fields.Char()
    occupation = fields.Char()
    emergency_name = fields.Char(string='Emergency Contact')
    emergency_phone = fields.Char(string='Emergency Phone')
    preferred_dentist_id = fields.Many2one('dental.dentist', string='Preferred Dentist')
    insurance_provider = fields.Char()
    insurance_number = fields.Char(string='Policy No.')
    # medical history
    allergies = fields.Text(tracking=True)
    condition_ids = fields.Many2many('dental.medical.condition', string='Medical Conditions')
    current_medication = fields.Text()
    is_smoker = fields.Boolean(string='Smoker')
    is_pregnant = fields.Boolean(string='Pregnant')
    has_diabetes = fields.Boolean(string='Diabetic')
    has_hypertension = fields.Boolean(string='Hypertension')
    medical_notes = fields.Text()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    # relations
    appointment_ids = fields.One2many('dental.appointment', 'patient_id')
    treatment_ids = fields.One2many('dental.treatment', 'patient_id')
    prescription_ids = fields.One2many('dental.prescription', 'patient_id')
    plan_ids = fields.One2many('dental.treatment.plan', 'patient_id')
    tooth_line_ids = fields.One2many('dental.tooth.line', 'patient_id')
    xray_ids = fields.One2many('dental.xray', 'patient_id')
    lab_order_ids = fields.One2many('dental.lab.order', 'patient_id')
    chart_html = fields.Html(compute='_compute_chart_html', sanitize=False)
    appointment_count = fields.Integer(compute='_compute_counts')
    treatment_count = fields.Integer(compute='_compute_counts')
    prescription_count = fields.Integer(compute='_compute_counts')
    invoice_count = fields.Integer(compute='_compute_counts')
    last_visit = fields.Datetime(compute='_compute_counts')

    @api.depends('birth_date')
    def _compute_age(self):
        today = date.today()
        for rec in self:
            b = rec.birth_date
            rec.age = (today.year - b.year - ((today.month, today.day) < (b.month, b.day))) if b else 0

    @api.depends('appointment_ids.state', 'treatment_ids.invoice_id', 'prescription_ids')
    def _compute_counts(self):
        for rec in self:
            rec.appointment_count = len(rec.appointment_ids)
            rec.treatment_count = len(rec.treatment_ids)
            rec.prescription_count = len(rec.prescription_ids)
            rec.invoice_count = len(rec.treatment_ids.invoice_id)
            done = rec.appointment_ids.filtered(lambda a: a.state == 'done')
            rec.last_visit = max(done.mapped('start_datetime')) if done else False

    @api.depends('tooth_line_ids.condition', 'tooth_line_ids.date')
    def _compute_chart_html(self):
        labels = dict(self.env['dental.tooth.line']._fields['condition'].selection)
        divider = '<div style="width:2px;background:#9bb5ae;margin:0 4px;"></div>'
        for rec in self:
            state = {}
            for line in rec.tooth_line_ids.sorted(lambda l: (l.date or date.min, l.id)):
                state[line.tooth_number] = line.condition

            def tooth(n):
                cond = state.get(str(n), 'healthy')
                fg = '#0e2a33' if cond in ('healthy', 'sealant', 'crown') else '#fff'
                return (
                    '<div title="Tooth %s: %s" style="width:38px;height:46px;margin:2px;'
                    'border-radius:9px 9px 16px 16px;background:%s;color:%s;border:1px solid #9bb5ae;'
                    'display:flex;align-items:center;justify-content:center;font-weight:600;'
                    'font-size:12px;">%s</div>' % (n, labels.get(cond), CONDITION_COLORS[cond], fg, n))

            def arch(left, right):
                return ('<div style="display:flex;justify-content:center;">%s%s%s</div>' % (
                    ''.join(tooth(n) for n in left), divider, ''.join(tooth(n) for n in right)))

            legend = ''.join(
                '<span style="display:inline-flex;align-items:center;margin:2px 10px 2px 0;font-size:12px;">'
                '<i style="width:12px;height:12px;border-radius:3px;background:%s;border:1px solid #9bb5ae;'
                'margin-right:4px;"></i>%s</span>' % (CONDITION_COLORS[k], v) for k, v in labels.items())
            rec.chart_html = (
                '<div style="overflow-x:auto;padding:8px 0;">'
                '<div style="text-align:center;font-size:11px;color:#6b7c85;">Upper arch (patient right to left)</div>'
                '%s<div style="height:10px;"></div>%s'
                '<div style="text-align:center;font-size:11px;color:#6b7c85;">Lower arch (patient right to left)</div>'
                '<div style="margin-top:10px;text-align:center;">%s</div></div>' % (
                    arch(range(18, 10, -1), range(21, 29)),
                    arch(range(48, 40, -1), range(31, 39)),
                    legend))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code') or vals['code'] == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('dental.patient') or 'New'
            if not vals.get('partner_id'):
                partner = self.env['res.partner'].create({
                    'name': vals.get('name'), 'phone': vals.get('phone'),
                    'email': vals.get('email'), 'street': vals.get('street'),
                    'city': vals.get('city'),
                })
                vals['partner_id'] = partner.id
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        sync = {k: vals[k] for k in ('name', 'phone', 'email', 'street', 'city') if k in vals}
        if sync:
            for rec in self.filtered('partner_id'):
                rec.partner_id.write(sync)
        return res

    def _open(self, name, model, domain, view_mode='list,form'):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': name, 'res_model': model,
            'view_mode': view_mode, 'domain': domain,
            'context': {'default_patient_id': self.id},
        }

    def action_view_appointments(self):
        return self._open('Appointments', 'dental.appointment', [('patient_id', '=', self.id)],
                          'list,calendar,form')

    def action_view_treatments(self):
        return self._open('Treatments', 'dental.treatment', [('patient_id', '=', self.id)])

    def action_view_prescriptions(self):
        return self._open('Prescriptions', 'dental.prescription', [('patient_id', '=', self.id)])

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': 'Invoices', 'res_model': 'account.move',
            'view_mode': 'list,form', 'domain': [('id', 'in', self.treatment_ids.invoice_id.ids)],
        }

    def action_new_appointment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': 'Book Appointment',
            'res_model': 'dental.appointment', 'view_mode': 'form', 'target': 'current',
            'context': {'default_patient_id': self.id,
                        'default_dentist_id': self.preferred_dentist_id.id},
        }
