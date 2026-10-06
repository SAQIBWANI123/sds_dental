from odoo import api, fields, models


class DentalPrescription(models.Model):
    _name = 'dental.prescription'
    _description = 'Prescription'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', default='New', readonly=True, copy=False)
    patient_id = fields.Many2one('dental.patient', required=True, tracking=True)
    dentist_id = fields.Many2one('dental.dentist', required=True)
    treatment_id = fields.Many2one('dental.treatment')
    date = fields.Date(default=fields.Date.context_today, required=True)
    diagnosis = fields.Char()
    line_ids = fields.One2many('dental.prescription.line', 'prescription_id', copy=True)
    notes = fields.Text(string='Advice / Notes')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.prescription') or 'New'
        return super().create(vals_list)


class DentalPrescriptionLine(models.Model):
    _name = 'dental.prescription.line'
    _description = 'Prescription Line'

    prescription_id = fields.Many2one('dental.prescription', required=True, ondelete='cascade')
    medicine_id = fields.Many2one('dental.medicine', required=True)
    dosage = fields.Char(compute='_compute_dosage', store=True, readonly=False)
    frequency = fields.Selection([
        ('od', 'Once a day'), ('bd', 'Twice a day'), ('tds', 'Three times a day'),
        ('qid', 'Four times a day'), ('sos', 'When needed'), ('hs', 'At bedtime')], default='bd')
    duration_days = fields.Integer(string='Days', default=5)
    timing = fields.Selection([('before', 'Before food'), ('after', 'After food'), ('any', 'Any time')],
                              default='after')
    instructions = fields.Char()

    @api.depends('medicine_id')
    def _compute_dosage(self):
        for line in self:
            line.dosage = line.medicine_id.default_dosage or line.medicine_id.strength
