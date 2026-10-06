from odoo import api, fields, models

from .common import SURFACES, TEETH


class DentalTreatmentPlan(models.Model):
    _name = 'dental.treatment.plan'
    _description = 'Treatment Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', default='New', readonly=True, copy=False)
    patient_id = fields.Many2one('dental.patient', required=True, tracking=True)
    dentist_id = fields.Many2one('dental.dentist', required=True, tracking=True)
    date = fields.Date(default=fields.Date.context_today)
    valid_until = fields.Date()
    state = fields.Selection([
        ('proposed', 'Proposed'), ('accepted', 'Accepted'), ('in_progress', 'In Progress'),
        ('completed', 'Completed'), ('rejected', 'Rejected'),
    ], default='proposed', tracking=True)
    line_ids = fields.One2many('dental.plan.line', 'plan_id', copy=True)
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    amount_total = fields.Monetary(compute='_compute_amount', store=True, string='Estimate')
    treatment_id = fields.Many2one('dental.treatment', readonly=True, copy=False)
    notes = fields.Text()

    @api.depends('line_ids.subtotal')
    def _compute_amount(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('subtotal'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('dental.treatment.plan') or 'New'
        return super().create(vals_list)

    def action_accept(self):
        self.state = 'accepted'

    def action_reject(self):
        self.state = 'rejected'

    def action_complete(self):
        self.state = 'completed'

    def action_start_treatment(self):
        self.ensure_one()
        lines = [(0, 0, {
            'procedure_id': l.procedure_id.id, 'tooth_number': l.tooth_number,
            'surface': l.surface, 'quantity': l.quantity, 'price_unit': l.price_unit,
        }) for l in self.line_ids]
        treatment = self.env['dental.treatment'].create({
            'patient_id': self.patient_id.id, 'dentist_id': self.dentist_id.id,
            'line_ids': lines, 'notes': 'Created from plan %s' % self.name,
        })
        self.write({'treatment_id': treatment.id, 'state': 'in_progress'})
        return {'type': 'ir.actions.act_window', 'res_model': 'dental.treatment',
                'res_id': treatment.id, 'view_mode': 'form'}


class DentalPlanLine(models.Model):
    _name = 'dental.plan.line'
    _description = 'Treatment Plan Line'
    _order = 'phase, id'

    plan_id = fields.Many2one('dental.treatment.plan', required=True, ondelete='cascade')
    phase = fields.Selection([
        ('1', 'Phase 1 - Urgent'), ('2', 'Phase 2 - Disease Control'),
        ('3', 'Phase 3 - Restorative'), ('4', 'Phase 4 - Maintenance'),
    ], default='1', required=True)
    procedure_id = fields.Many2one('dental.procedure', required=True)
    tooth_number = fields.Selection(TEETH, string='Tooth')
    surface = fields.Selection(SURFACES)
    quantity = fields.Float(default=1.0)
    price_unit = fields.Monetary(compute='_compute_price', store=True, readonly=False)
    currency_id = fields.Many2one(related='plan_id.currency_id')
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True)

    @api.depends('procedure_id')
    def _compute_price(self):
        for line in self:
            line.price_unit = line.procedure_id.price

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit
