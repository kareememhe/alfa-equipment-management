import base64
import uuid

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class MaintenanceEquipment(models.Model):
    # _inherit adds our fields to Odoo's existing equipment model
    _inherit = 'maintenance.equipment'

    # ---------- Calibration ----------
    calibration_required = fields.Boolean(string='Requires Calibration', tracking=True)
    calibration_interval = fields.Integer(
        string='Calibration Interval (months)', default=12, tracking=True)
    last_calibration_date = fields.Date(string='Last Calibration', tracking=True)
    next_calibration_date = fields.Date(
        string='Next Calibration',
        compute='_compute_next_calibration_date',
        store=True,
    )
    calibration_status = fields.Selection(
        [('ok', 'Valid'), ('due_soon', 'Due Soon'), ('overdue', 'Overdue'),
         ('never', 'Never Calibrated')],
        string='Calibration Status',
        compute='_compute_calibration_status',
        store=True,  # stored so it can be grouped and charted on the dashboard
    )

    # ---------- QR code ----------
    qr_token = fields.Char(string='QR Token', copy=False, readonly=True, index=True)
    qr_url = fields.Char(string='Fault Report Link', compute='_compute_qr')
    qr_image = fields.Binary(string='QR Code', compute='_compute_qr')

    _sql_constraints = [
        ('qr_token_unique', 'unique(qr_token)', 'Each equipment must have a unique QR token.'),
    ]

    @api.depends('last_calibration_date', 'calibration_interval')
    def _compute_next_calibration_date(self):
        for equipment in self:
            if equipment.last_calibration_date and equipment.calibration_interval:
                equipment.next_calibration_date = (
                    equipment.last_calibration_date
                    + relativedelta(months=equipment.calibration_interval)
                )
            else:
                equipment.next_calibration_date = False

    @api.depends('calibration_required', 'next_calibration_date')
    def _compute_calibration_status(self):
        today = fields.Date.context_today(self)
        for equipment in self:
            next_date = equipment.next_calibration_date
            if not equipment.calibration_required:
                equipment.calibration_status = False
            elif not equipment.last_calibration_date:
                # Needs calibration but has no record of ever being calibrated
                equipment.calibration_status = 'never'
            elif not next_date:
                equipment.calibration_status = False
            elif next_date < today:
                equipment.calibration_status = 'overdue'
            elif next_date <= today + relativedelta(days=30):
                equipment.calibration_status = 'due_soon'
            else:
                equipment.calibration_status = 'ok'

    @api.depends('qr_token')
    def _compute_qr(self):
        report = self.env['ir.actions.report']
        for equipment in self:
            if equipment.qr_token:
                # strip() guards against stray spaces/newlines in the web.base.url setting
                base_url = (equipment.get_base_url() or '').strip().rstrip('/')
                url = '%s/equipment/report/%s' % (base_url, equipment.qr_token)
                equipment.qr_url = url
                # quiet=0 keeps the white border (Odoo removes it by default for QR),
                # which phone cameras need; level M adds error correction for printed labels
                png = report.barcode('QR', url, width=300, height=300, quiet=0, barLevel='M')
                equipment.qr_image = base64.b64encode(png)
            else:
                equipment.qr_url = False
                equipment.qr_image = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault('qr_token', uuid.uuid4().hex)
        return super().create(vals_list)

    @api.model
    def _alfa_ensure_qr_tokens(self):
        # Runs on every install/upgrade so existing equipment also gets a token
        for equipment in self.with_context(active_test=False).search([('qr_token', '=', False)]):
            equipment.qr_token = uuid.uuid4().hex

    # ---------- Daily job ----------

    @api.model
    def _alfa_refresh_calibration_status(self):
        """Recompute the stored status for all equipment that needs calibration.
        Used by the daily job (the status depends on today's date) and on every
        module upgrade (so logic changes reach existing records immediately)."""
        equipment = self.with_context(active_test=False).search([])
        self.env.add_to_compute(self._fields['calibration_status'], equipment)
        self.env.flush_all()
        return equipment.filtered('calibration_required')

    @api.model
    def _cron_calibration_alerts(self):
        """Runs every day: refreshes statuses (they depend on today's date)
        and creates a To-Do for each piece of equipment due soon or overdue."""
        equipment = self._alfa_refresh_calibration_status()

        todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        admin = self.env.ref('base.user_admin', raise_if_not_found=False)
        summaries = {
            'due_soon': 'Calibration due',
            'overdue': 'Calibration overdue',
            'never': 'Calibration missing',
        }
        today = fields.Date.context_today(self)
        for item in equipment.filtered(lambda e: e.calibration_status in summaries):
            already_open = item.activity_ids.filtered(lambda a: a.summary in summaries.values())
            if already_open or not todo:
                continue
            responsible = item.technician_user_id or item.owner_user_id or admin
            if item.calibration_status == 'never':
                note = 'This equipment requires calibration but has never been calibrated.'
            else:
                note = 'Next calibration date: %s' % item.next_calibration_date
            item.activity_schedule(
                activity_type_id=todo.id,
                date_deadline=item.next_calibration_date or today,
                summary=summaries[item.calibration_status],
                note=note,
                user_id=responsible.id,
            )
