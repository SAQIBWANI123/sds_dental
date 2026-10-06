from odoo import fields, models
from .common import SURFACES  # noqa: F401


class DentalProcedure(models.Model):
    _name = 'dental.procedure'
    _description = 'Dental Procedure'
    _order = 'category, name'

    name = fields.Char(required=True)
    code = fields.Char()
    category = fields.Selection([
        ('diagnostic', 'Diagnostic'), ('preventive', 'Preventive'),
        ('restorative', 'Restorative'), ('endodontic', 'Endodontic'),
        ('periodontic', 'Periodontic'), ('prosthodontic', 'Prosthodontic'),
        ('orthodontic', 'Orthodontic'), ('surgery', 'Oral Surgery'),
        ('cosmetic', 'Cosmetic'),
    ], default='diagnostic', required=True)
    price = fields.Monetary(currency_field='currency_id')
    duration = fields.Float(default=0.5, help='Estimated duration in hours')
    description = fields.Text()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')


class DentalRoom(models.Model):
    _name = 'dental.room'
    _description = 'Dental Room / Chair'

    name = fields.Char(required=True)
    code = fields.Char()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)


class DentalMedicine(models.Model):
    _name = 'dental.medicine'
    _description = 'Medicine'
    _order = 'name'

    name = fields.Char(required=True)
    form = fields.Selection([
        ('tablet', 'Tablet'), ('capsule', 'Capsule'), ('syrup', 'Syrup'),
        ('gel', 'Gel'), ('mouthwash', 'Mouthwash'), ('injection', 'Injection'),
        ('other', 'Other')], default='tablet')
    strength = fields.Char(help='e.g. 500 mg')
    default_dosage = fields.Char()
    notes = fields.Text()
    active = fields.Boolean(default=True)


class DentalMedicalCondition(models.Model):
    _name = 'dental.medical.condition'
    _description = 'Medical Condition'

    name = fields.Char(required=True)
    color = fields.Integer()
