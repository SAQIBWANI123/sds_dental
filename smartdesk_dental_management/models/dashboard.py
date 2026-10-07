from datetime import datetime, time, timedelta

import pytz

from odoo import api, fields, models

STATE_LABELS = {
    'draft': 'Draft', 'confirmed': 'Confirmed', 'checked_in': 'Checked In',
    'in_progress': 'In Progress', 'done': 'Done', 'cancelled': 'Cancelled', 'no_show': 'No Show',
}
STATE_COLORS = {
    'draft': '#94a3b8', 'confirmed': '#3b82f6', 'checked_in': '#06b6d4',
    'in_progress': '#f59e0b', 'done': '#16a34a', 'cancelled': '#ef4444', 'no_show': '#a855f7',
}


class DentalDashboard(models.AbstractModel):
    _name = 'dental.dashboard'
    _description = 'Dental Dashboard Data Provider'

    @api.model
    def get_data(self):
        env = self.env
        tz = pytz.timezone(env.user.tz or 'UTC')
        today = fields.Date.context_today(self)

        def utc(d, t=time.min):
            return tz.localize(datetime.combine(d, t)).astimezone(pytz.utc).replace(tzinfo=None)

        def local(dt):
            return pytz.utc.localize(dt).astimezone(tz)

        day_start, day_end = utc(today), utc(today + timedelta(days=1))
        week_end = utc(today + timedelta(days=8))
        month_start = today.replace(day=1)
        Appointment, Treatment = env['dental.appointment'], env['dental.treatment']

        today_appts = Appointment.search([
            ('start_datetime', '>=', day_start), ('start_datetime', '<', day_end),
            ('state', '!=', 'cancelled')], order='start_datetime')
        upcoming = Appointment.search_count([
            ('start_datetime', '>=', day_end), ('start_datetime', '<', week_end),
            ('state', 'in', ('draft', 'confirmed'))])
        month_treat = Treatment.search([('date', '>=', month_start), ('state', '=', 'done')])
        invoiced = Treatment.search([('invoice_id.state', '=', 'posted')])
        outstanding = sum(invoiced.invoice_id.mapped('amount_residual'))

        # revenue over the last 6 months
        revenue = []
        cursor = month_start
        months = []
        for _i in range(6):
            months.append(cursor)
            cursor = (cursor - timedelta(days=1)).replace(day=1)
        for m in reversed(months):
            nxt = (m + timedelta(days=32)).replace(day=1)
            recs = Treatment.search([('date', '>=', m), ('date', '<', nxt), ('state', '=', 'done')])
            revenue.append({'label': m.strftime('%b'), 'value': sum(recs.mapped('amount_total'))})

        # appointments by state (this month)
        grouped = Appointment._read_group(
            [('start_datetime', '>=', utc(month_start))], ['state'], ['__count'])
        by_state = [{'key': st, 'label': STATE_LABELS[st], 'color': STATE_COLORS[st], 'count': cnt}
                    for st, cnt in grouped]

        top = env['dental.treatment.line']._read_group(
            [('treatment_id.state', '=', 'done'), ('date', '>=', today.replace(month=1, day=1))],
            ['procedure_id'], ['subtotal:sum', '__count'], order='subtotal:sum desc', limit=5)
        top_procedures = [{'name': p.name, 'amount': amt, 'count': cnt} for p, amt, cnt in top]

        genders = env['dental.patient']._read_group([], ['gender'], ['__count'])
        gender_labels = {'male': 'Male', 'female': 'Female', 'other': 'Other', False: 'Not set'}
        dentists = Appointment._read_group(
            [('start_datetime', '>=', utc(month_start)), ('state', '=', 'done')],
            ['dentist_id'], ['__count'], order='__count desc', limit=5)

        return {
            'currency': env.company.currency_id.symbol,
            'kpis': {
                'patients': env['dental.patient'].search_count([]),
                'new_patients': env['dental.patient'].search_count([('create_date', '>=', utc(month_start))]),
                'today': len(today_appts),
                'today_done': len(today_appts.filtered(lambda a: a.state == 'done')),
                'upcoming': upcoming,
                'treatments_open': Treatment.search_count([('state', 'in', ('draft', 'in_progress'))]),
                'revenue_month': sum(month_treat.mapped('amount_total')),
                'outstanding': outstanding,
                'plans_open': env['dental.treatment.plan'].search_count([('state', 'in', ('proposed', 'accepted'))]),
                'lab_pending': env['dental.lab.order'].search_count([('state', '=', 'sent')]),
                'dentists': env['dental.dentist'].search_count([]),
                'prescriptions_month': env['dental.prescription'].search_count([('date', '>=', month_start)]),
            },
            'today_appointments': [{
                'id': a.id, 'time': local(a.start_datetime).strftime('%H:%M'),
                'patient': a.patient_id.name, 'dentist': a.dentist_id.name,
                'reason': a.reason or '', 'state': a.state, 'state_label': STATE_LABELS[a.state],
                'color': STATE_COLORS[a.state],
            } for a in today_appts],
            'revenue': revenue,
            'by_state': by_state,
            'top_procedures': top_procedures,
            'genders': [{'label': gender_labels.get(g, 'Not set'), 'count': c} for g, c in genders],
            'dentist_load': [{'name': d.name, 'count': c} for d, c in dentists],
        }
