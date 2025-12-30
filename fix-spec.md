# Fix Specification: Glucose Pumps Module

This document outlines the critical bugs, missing functionality, and UI improvements required for the `glucose_pumps_demo` module, based on a dry run of the Patient Journey.

## 1. Website: Holiday Pump Request Form (SKIP ME)
**Issue:** The URL `/holiday-pump-request` returns a 404 error.
**Requirement:**
- Create a website controller to handle `GET` and `POST` requests for `/holiday-pump-request`.
- Create a website template with a form containing:
    - Patient Name
    - Main Pump Serial Number
    - Mobile Number
    - Travel Dates (Start/End)
    - Destination
    - Additional Notes
- **Logic:**
    - Validate that the Serial Number exists and is currently assigned to a patient (case-insensitive).
    - On submission, create a `glucose.holiday.pump.request` record.
    - Trigger an email notification to the helpdesk email configured in settings.
**Testing:**
- Navigate to `/holiday-pump-request` as a public user.
- Submit the form with a valid SN (e.g., `sn-pri-0007`) and verify record creation in Odoo.

## 2. Consumables: Logic & Initialization (Critical)
**Issue:** Thresholds are hardcoded (10/13) in `glucose.consumables.allocation`, and records are not auto-created.
**Requirement:**
- **Settings Integration:** Update the `_compute_threshold_status` (or equivalent) in `glucose.consumables.allocation` to use the global thresholds from `res.config.settings`.
- **Auto-Initialization:** Add a hook (e.g., in `res.partner.create` or a dedicated method) to create a `glucose.consumables.allocation` record for the current month when a new patient is created.
- **UI Labels:** Ensure status labels match the journey: "Normal", "Warning", "Exceeded" (with appropriate colors).
**Testing:**
- Change global thresholds in Settings.
- Create a new patient and verify a consumable record is created for the current month.
- Update usage and verify the status changes based on the *new* thresholds.

## 3. Equipment: Replacement Date & Alerts (Critical)
**Issue:** `replacement_date` is missing from the UI, and alerts don't trigger.
**Requirement:**
- **UI:** Add `replacement_date` to the `stock.lot` form view (under Glucose Pump Info).
- **Logic:** Automatically calculate `replacement_date` as 4 years after `installation_date` when a device is assigned.
- **Alerts:** Ensure the "Check Replacement Date Alerts" cron job correctly identifies devices within the threshold (configured in settings) and creates activities for "Patient Administrators".
**Testing:**
- Assign a device to a patient and verify `replacement_date` is set to +4 years.
- Manually set a `replacement_date` to 15 days from now.
- Run the cron job and verify an activity is created.

## 4. Assignment Logs: Duplicate Records
**Issue:** Saving a patient creates duplicate `glucose.assignment.log` records.
**Requirement:**
- Investigate the `write` and `create` methods in `res.partner` or the assignment logic.
- Ensure only one log is created per device assignment.
**Testing:**
- Create a patient with a primary and holiday pump.
- Verify only 2 logs exist (one for each device).

## 5. UI/UX Improvements
**Requirement:**
- **Form Actions:** Add "Unassign Device" and "Scrap Device" buttons to the `stock.lot` form view header (currently only in List View).
- **Patient Chatter:** Ensure that when a device is assigned/unassigned, a note is posted to the **Patient's** chatter, not just the Equipment's chatter.
- **Menu Consistency:** Ensure all menu paths match the `patient-journey.md` (e.g., "Equipment" instead of "Glucose Pumps" where applicable).
**Testing:**
- Open an Equipment record and verify "Unassign" button is visible and functional.
- Assign a device and check the Patient's chatter for the log.

## Context for Implementation
- **Odoo Version:** 18.0
- **Module Name:** `glucose_pumps_demo`
- **Key Models:** `stock.lot`, `res.partner`, `glucose.assignment.log`, `glucose.consumables.allocation`, `glucose.holiday.pump.request`.
