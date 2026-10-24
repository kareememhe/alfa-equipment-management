from odoo import _, http
from odoo.http import request
from odoo.tools import plaintext2html

PRIORITIES = ('1', '2', '3')
MAX_PHOTO_SIZE = 10 * 1024 * 1024  # 10 MB


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
            values.update(reporter_name=reporter, description=description)

            # Optional photo of the problem
            photo = post.get('photo')
            photo_data = None
            if photo and getattr(photo, 'filename', ''):
                if not (photo.mimetype or '').startswith('image/'):
                    values['error'] = 'photo'
                else:
                    photo_data = photo.read()
                    if len(photo_data) > MAX_PHOTO_SIZE:
                        values['error'] = 'photo_size'

            if not reporter or not description:
                values['error'] = 'missing'

            if not values['error']:
                maintenance_request = request.env['maintenance.request'].sudo().with_context(
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
                if photo_data:
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': photo.filename,
                        'raw': photo_data,
                        'res_model': 'maintenance.request',
                        'res_id': maintenance_request.id,
                    })
                    maintenance_request.message_post(
                        body=_('Photo attached by %s', reporter),
                        attachment_ids=attachment.ids,
                    )
                maintenance_request._alfa_notify_managers_of_qr_report()
                values['maintenance_request'] = maintenance_request

        return request.render('alfa_equipment.qr_report_page', values)
