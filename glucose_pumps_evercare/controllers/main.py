from odoo import http
from odoo.http import request


class HolidayPumpController(http.Controller):

    @http.route(['/holiday-pump-request'], type='http', auth="public", website=True)
    def holiday_pump_request_form(self, **post):
        if post:
            # Validate Serial Number
            sn = post.get('main_pump_serial', '').strip()
            lot = request.env['stock.lot'].sudo().search([
                ('name', '=ilike', sn),
                ('is_glucose_pump', '=', True),
                ('pump_state', '=', 'assigned')
            ], limit=1)
            
            if not lot:
                return request.render("glucose_pumps_evercare.holiday_pump_request_error", {
                    'error_msg': f"Serial Number '{sn}' not found or not currently assigned to a patient."
                })
            
            # Create the request record
            vals = {
                'patient_name': post.get('patient_name'),
                'main_pump_serial': sn,
                'contact_phone': post.get('contact_phone'),
                'contact_email': post.get('contact_email'),
                'travel_start_date': post.get('travel_start_date'),
                'travel_end_date': post.get('travel_end_date'),
                'destination': post.get('destination'),
                'reason': post.get('reason'),
                'additional_notes': post.get('additional_notes'),
                'patient_id': lot.assigned_patient_id.id,
                'status': 'pending',
            }
            
            request_record = request.env['glucose.holiday.pump.request'].sudo().create(vals)
            
            # Trigger email notification (Logic to be implemented in the model or here)
            # For now, we just show the success page
            return request.render("glucose_pumps_evercare.holiday_pump_request_success", {
                'request_name': request_record.name
            })

        return request.render("glucose_pumps_evercare.holiday_pump_request_template")
