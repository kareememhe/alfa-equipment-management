from odoo import _, fields, models
from odoo.exceptions import UserError


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    approval_state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('to_approve', 'Waiting Approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Approval',
        default='draft',
        copy=False,
        tracking=True,  # every change is logged in the chatter
    )
    approved_by_id = fields.Many2one(
        'res.users', string='Approved By', readonly=True, copy=False, tracking=True)
    approval_date = fields.Datetime(
        string='Approval Date', readonly=True, copy=False, tracking=True)
    rejection_reason = fields.Text(string='Rejection Reason', copy=False)

    # Filled in when a fault is reported by scanning the equipment's QR code
    reported_by_name = fields.Char(string='Reported By', readonly=True)
    report_source = fields.Selection(
        [('internal', 'Internal'), ('qr', 'QR Code')],
        string='Source', default='internal', readonly=True)

    # ---------- Buttons ----------

    def action_submit_for_approval(self):
        for request in self:
            if request.approval_state not in ('draft', 'rejected'):
                raise UserError(_("Only draft or rejected requests can be submitted."))
        self.write({'approval_state': 'to_approve', 'rejection_reason': False})

    def action_approve(self):
        self._check_is_manager()
        self.write({
            'approval_state': 'approved',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })

    def action_reject(self):
        self._check_is_manager()
        for request in self:
            if not request.rejection_reason:
                raise UserError(_("Please write a rejection reason before rejecting."))
        self.write({'approval_state': 'rejected'})
        for request in self:
            request.message_post(body=_("Rejected: %s", request.rejection_reason))

    # ---------- Rules ----------

    def _check_is_manager(self):
        # Checked on the server too, not only by hiding the button
        if not self.env.user.has_group('maintenance.group_equipment_manager'):
            raise UserError(_("Only maintenance managers can approve or reject requests."))

    def write(self, vals):
        # A request cannot be closed as done unless it was approved
        if vals.get('stage_id'):
            stage = self.env['maintenance.stage'].browse(vals['stage_id'])
            if stage.done and self.filtered(lambda r: r.approval_state != 'approved'):
                raise UserError(_("This request must be approved before it can be closed."))
        return super().write(vals)
