{
    'name': 'Dental Management System',
    'version': '19.0.1.0.0',
    'summary': 'Complete dental clinic management: patients, appointments, dental chart, treatments, prescriptions, lab orders, invoicing and dashboard.',
    'description': """
Dental Management System
========================
All-in-one dental clinic management for Odoo 19 by SmartDeskSolutions.

* Patient records with medical history, allergies and insurance
* Visual dental chart (odontogram, FDI notation)
* Appointment scheduling with calendar, conflict detection and email reminders
* Treatments with per-tooth procedures and one-click invoicing
* Treatment plans with phases and estimates
* Prescriptions with printable PDF
* Dental lab orders, X-ray / document storage
* Dentists, rooms, procedures catalogue and medicines
* Interactive dashboard with KPIs and charts
    """,
    'author': 'SmartDeskSolutions',
    'maintainer': 'SmartDeskSolutions',
    'website': 'https://www.smartdesksolutions.com',
    'support': 'info@smartdesksolutions.com',
    'category': 'Healthcare',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'account', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/dental_data.xml',
        'data/mail_template.xml',
        'data/cron.xml',
        'report/prescription_report.xml',
        'report/treatment_report.xml',
        'views/dentist_views.xml',
        'views/config_views.xml',
        'views/patient_views.xml',
        'views/appointment_views.xml',
        'views/treatment_views.xml',
        'views/plan_views.xml',
        'views/prescription_views.xml',
        'views/clinical_views.xml',
        'views/dashboard_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'smartdesk_dental_management/static/src/dashboard/dashboard.js',
            'smartdesk_dental_management/static/src/dashboard/dashboard.xml',
            'smartdesk_dental_management/static/src/dashboard/dashboard.scss',
        ],
    },
    'images': ['static/description/banner.png'],
    'post_init_hook': 'post_init_hook',
    'application': True,
    'installable': True,
    'auto_install': False,
}
