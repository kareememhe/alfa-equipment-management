from odoo import _, http
from odoo.http import request
from odoo.tools import plaintext2html

PRIORITIES = ('1', '2', '3')


class EquipmentQrReport(http.Controller):

    @http.route('/equipment/report/<string:token>', type='http', auth='public',
                methods=['GET', 'POST'], csrf=True)
    def report_fault(self, token, **post):
        # Public page: no login needed. The random token means people can only
        # reach equipment whose QR code they have physically scanned.
        equipment = request.env['maintenance.equipment'].sudo().search(
            [('qr_token', '=', token)], limit=1)
        if not equipment:
            return request.not_found()

        values = {'equipment': equipment, 'error': False, 'maintenance_request': False}

        if request.httprequest.method == 'POST':
            reporter = (post.get('reporter_name') or '').strip()
            description = (post.get('description') or '').strip()
            priority = post.get('priority') if post.get('priority') in PRIORITIES else '2'

            if not reporter or not description:
                values['error'] = True
                values.update(reporter_name=reporter, description=description)
            else:
                values['maintenance_request'] = request.env['maintenance.request'].sudo().with_context(
                    mail_create_nosubscribe=True,
                ).create({
                    'name': _('Fault reported: %s', equipment.name),
                    'equipment_id': equipment.id,
                    'description': plaintext2html(description),
                    'priority': priority,
                    'reported_by_name': reporter,
                    'report_source': 'qr',
                    'owner_user_id': False,
                })

        return request.render('alfa_equipment.qr_report_page', values)
