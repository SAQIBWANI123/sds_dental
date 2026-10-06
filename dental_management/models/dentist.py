from odoo import api, fields, models


class DentalDentist(models.Model):
    _name = 'dental.dentist'
    _description = 'Dentist'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Related User')
    image_1920 = fields.Image(max_width=1920, max_height=1920)
    image_128 = fields.Image(related='image_1920', max_width=128, max_height=128, store=True)
    specialization = fields.Selection([
        ('general', 'General Dentistry'), ('orthodontics', 'Orthodontics'),
        ('endodontics', 'Endodontics'), ('periodontics', 'Periodontics'),
        ('prosthodontics', 'Prosthodontics'), ('pediatric', 'Pediatric Dentistry'),
        ('oral_surgery', 'Oral & Maxillofacial Surgery'), ('cosmetic', 'Cosmetic Dentistry'),
    ], default='general', required=True)
    license_no = fields.Char(string='License No.')
    phone = fields.Char()
    email = fields.Char()
    consultation_fee = fields.Monetary(currency_field='currency_id')
    color = fields.Integer()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    notes = fields.Text()
    appointment_count = fields.Integer(compute='_compute_counts')
    patient_count = fields.Integer(compute='_compute_counts')

    def _compute_counts(self):
        for rec in self:
            appts = self.env['dental.appointment'].search([('dentist_id', '=', rec.id)])
            rec.appointment_count = len(appts)
            rec.patient_count = len(appts.patient_id)

    def action_view_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': 'Appointments',
            'res_model': 'dental.appointment', 'view_mode': 'list,calendar,form',
            'domain': [('dentist_id', '=', self.id)],
            'context': {'default_dentist_id': self.id},
        }
