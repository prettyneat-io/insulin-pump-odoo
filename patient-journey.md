# Patient Journey (End-to-End)

This single journey is designed to touch every feature described in `spec.md`, using one patient and a small set of devices, locations, consumables, and staff roles.

## Cast (Roles)

- **Patient Administrators** (internal Odoo users; e.g., Jonathan, Denise)
  - Full access to the Glucose Pump app
  - Manage Patients menu under Glucose Pumps
  - Can assign/unassign/scrap/replace devices
  - Receive replacement-date alert activities
- **Patient** (public website visitor)
  - Can submit Holiday Pump Request Form without login
- **Helpdesk mailbox**
  - Receives email notifications from holiday pump requests at `tandemsupport@evercaremedical.eu`

## Configuration Setup (Admin)

> Goal: Ensure module configuration and constraints are exercised.

1. **Open**: Glucose Pump App → Configuration → **Settings**
2. Configure:
   - **Allowed pump products** (devices searchable/assignable in the app):
     - `Tandem t:slim X2 Pump` (standard product)
   - **RMA replacement product**:
     - `Tandem t:slim X2 Pump (RMA)`
   - **Returns location** (Internal Location):
     - Default to `WH/Evercare Medical/Insulin Pumps`
   - **Replacement date alert threshold**:
     - Set to `30` days
   - **Consumables thresholds**:
     - Enable threshold warnings
     - Set global monthly threshold (example): `10`
   - **Helpdesk email configuration**:
     - Incoming/outgoing: `tandemsupport@evercaremedical.eu`

Expected results:
- Standard devices can be assigned initially.
- RMA devices cannot be used except via the Replace Device workflow.
- Search/selection for SNs only considers the configured products.

## Training Locations Setup (Admin)

1. **Open**: Glucose Pump App → Configuration → **Training Locations**
2. Create at least one active record:
   - Name: `Mosta Clinic`

Expected results:
- Training location is selectable on patient creation/edit.
- Training location is visible in Patients Index.

## Device Stock Setup (Admin)

> We will create three device serials to cover standard assignment, holiday assignment, and RMA replacement.

Create the following Equipment/Lot records (Inventory lot/serial records, extended by this module):

- **Standard primary device**
  - SN: `SN-PRI-0007`
  - Product: `Tandem t:slim X2 Pump`
  - State: `Available` (default)
- **Standard holiday pump**
  - SN: `SN-HOL-0012`
  - Product: `Tandem t:slim X2 Pump`
  - State: `Available` (default)
- **RMA replacement device**
  - SN: `SN-RMA-0099`
  - Product: `Tandem t:slim X2 Pump (RMA)`
  - State: `Available` (default)

On each Equipment record:
- Verify the **State** selection exists with: `Available`, `Assigned`, `Scrapped`.
- Verify **Chatter** is enabled.
- Verify the **Linked Patient Information** tab exists (will be empty until assignment).

## Patient Creation (Create Patient Modal)

> This step touches the Create Patient Modal, patient-only constraints, patient internal ID sequence, initial assignment logs, and chatter.

1. **Open**: Glucose Pump App → **Patients** (Patients Index Page)
2. Click **Create Patient**
3. Enter patient contact information (example):
   - Name: `Alex Camilleri`
   - Email: `alex@example.com`
   - Phone: `+356 9999 1111`
   - Individual (not company)
4. Fill Patient Info fields:
   - Patient Date of Birth: `1990-04-12`
   - Patient ID Number: `MT-1234567`
   - Patient Phone: `+356 9999 1111`
   - Patient Locality: `Mosta`
5. Assign devices in the modal:
   - **Select Primary Device SN**: `SN-PRI-0007`
   - **Select Holiday Pump SN (optional)**: `SN-HOL-0012`
   - **Holiday Pump Return Date**: `2026-01-20` (mandatory when holiday pump selected)
   - **Installation Date**: default today (editable)
   - **Training Location**: `Mosta Clinic`

Validation expectations:
- Only Individuals can be marked as patient.
- The patient is created with **IsPatient = true**.
- **Patient Internal ID** is auto-generated in year-based format, e.g. `2025-001`.
- RMA device `SN-RMA-0099` is **not available** in the initial primary/holiday selectors.
- If Holiday Pump SN is set, Holiday Pump Return Date is required.

System effects:
- The selected Equipment states become `Assigned`.
- Assignment logs are created:
  - For `SN-PRI-0007` with assignment type `primary` and installation date = chosen date
  - For `SN-HOL-0012` with assignment type `holiday_pump` and installation date = chosen date
- Chatter entries appear:
  - On the Patient contact: notes reflecting device assignment(s)
  - On each Equipment record: note indicating assigned to Patient ID `2025-001` and assignment type

## Patients Menu (Filtered View)

> This step touches the Patients menu and UI rules.

1. **Open**: Glucose Pumps → **Patients**
2. Confirm:
   - Only contacts with `IsPatient = true` are listed.
   - Card view shows **Patient Internal ID**.
   - The button reads **New Patient** (and creates a Contact with `IsPatient = true`).
   - Default phone/mobile fields are hidden in the Patient view.

## Equipment Index Page (Dashboard + Navigation)

> This step touches the dashboard counts, default Equipment view, Patients tab navigation, and row click behavior.

1. **Open**: Glucose Pump App → **Equipment**
2. Confirm header cards display counts for:
   - Assigned
   - Unassigned
   - Scrapped
3. In the **Devices** view (default), confirm columns include:
   - Patient Internal ID
   - Patient Name
   - Equipment SN
   - Assignment Type (Primary / Holiday Pump)
   - Upcoming Activities
   - Installation Date
4. Click the row for `SN-PRI-0007` → navigates to the Equipment (Lot/SN) page.

## Equipment Page (Linked Patient Information + History)

> This step touches the Equipment page changes.

On Equipment record `SN-PRI-0007`:
- Open the **Linked Patient Information** tab.
- Confirm it pulls patient data from Contacts (Alex Camilleri).
- Confirm the assignment history shows:
  - installation date
  - replacement date (empty for now)
  - assignment type
- Confirm chatter is present and contains assignment notes.

Repeat quick verification for `SN-HOL-0012` (assignment type shown as holiday pump).

## Consumables Allocation + Tracking

> This step touches the Consumables page, thresholds, warnings, and “no auto sales orders”.

1. **Open**: Glucose Pump App → **Consumables** (Consumables Tracking Page)
2. Allocate consumables for Alex for the current month/year:
   - Quantity Allocated: `10` (uses global default unless overridden)
   - Quantity Used: `9`
3. Confirm threshold indicator:
   - `9` used → **Green** (10 or less)
4. Update usage to `12`:
   - Confirm indicator becomes **Orange** (11–13)
5. Set allocated to `14` (or set used > 13 if warnings are defined that way in your implementation):
   - Confirm warning text: `Charge for additional pumps`
6. Confirm **no Sales Order** is created automatically when usage exceeds allocation.

## Replacement Date Alert (Scheduled Action)

> This step touches the automated daily alert that creates activities.

1. On `SN-PRI-0007`, set (or simulate) a replacement date such that it falls within 30 days.
2. Wait for the scheduled job (or run it manually as an admin in Odoo).

Expected results:
- An **activity** is created on the Equipment record.
- Assigned to **Patient Administrators**.
- Includes:
  - Equipment SN
  - Patient Internal ID + Name
  - Assignment Type
  - Replacement Date
  - Days remaining
- The activity appears under **Upcoming Activities** on the Devices Index page row.

## Holiday Pump Request (Public Website Form)

> This step touches the public form, serial validation, helpdesk routing, and email notification.

1. As a public user (no login), open the **Holiday Pump Request Form**.
2. Enter:
   - Patient Name: `Alex Camilleri`
   - Main Pump Serial Number: `sn-pri-0007` (lowercase on purpose)
   - Mobile Number: `+356 9999 1111`
   - Travel Dates: `2026-02-10` to `2026-02-24`
   - Destination: `Rome`
   - Additional Notes: `Carrying extra supplies`
3. Submit.

Validation expectations:
- The serial number match is **case-insensitive**.
- The serial must exist and be attached to a patient; otherwise submission is blocked.

System effects:
- A **Holiday Pump Request** record is created with status `pending` and a submitted date.
- The request lands in the **Holiday Pump Helpdesk** queue.
- An email notification is sent to the helpdesk configuration (`tandemsupport@evercaremedical.eu`).

## Unassign Holiday Pump (Device Action)

> This step touches the Devices Index action menu and unassignment requirements.

Scenario: Alex returns from travel early; holiday pump is no longer needed.

1. **Open**: Glucose Pump App → **Equipment**
2. Select the row for `SN-HOL-0012` (holiday pump) in the **List View**.
3. Click **Actions** → **Unassign Device**

Expected system effects:
- Device is unlinked from patient.
- Device is transferred back to the configured **Returns location**.
- Chatter messages:
  - On Patient: `Holiday Pump SN SN-HOL-0012 unassigned.`
  - On Device: `Patient ID 2025-001 unassigned (holiday pump)`
- Equipment state becomes `Available`.

## Replace Primary Device (Replace Device Modal + RMA Constraints)

> This step touches the Replace Device Modal, replacement reason/notes, RMA-only selection, state transitions, assignment logs, transfer to returns location, and chatter.

Scenario: The primary device malfunctions.

1. **Open**: Glucose Pump App → **Equipment**
2. Select the row for primary device `SN-PRI-0007`
3. Action → **Replace Device**
4. In the modal, confirm it displays current device info:
   - Current Device SN: `SN-PRI-0007`
   - Patient Name and Internal ID: `Alex Camilleri (2025-001)`
   - Installation Date
5. Fill fields:
   - Replacement Reason: `Malfunction`
   - Replacement Notes: `Intermittent shutdowns`
   - Select Replacement Device SN: `SN-RMA-0099`

Validation expectations:
- Only devices from the configured **RMA product** are selectable.
- Replacement device must be in state `Available`.

On confirmation, expected system effects:
- Old assignment log for `SN-PRI-0007` gets a **replacement date** set.
- Old device is unlinked from patient, state becomes `Available`, and is transferred to the **Returns location**.
- New RMA device `SN-RMA-0099` becomes the patient’s **primary** device:
  - state becomes `Assigned`
  - a new assignment log is created with installation date = today
- Chatter entries:
  - On Patient: `Primary device SN SN-PRI-0007 replaced with RMA device SN SN-RMA-0099. Reason: Malfunction`
  - On old Device: `Replaced for Patient ID 2025-001. Reason: Malfunction`
  - On new Device: `Assigned to Patient ID 2025-001 as replacement for SN SN-PRI-0007`

Constraint coverage:
- Attempting to assign `SN-RMA-0099` as an initial primary (Create Patient) or as a holiday pump must be prevented.
- Attempting to replace using a non-RMA device must be prevented.

## Scrap a Device (Device Action)

> This step touches the scrap flow, device state = scrapped, chatter, and dashboard counts.

Scenario: The old device `SN-PRI-0007` is diagnosed as non-repairable.

1. **Open**: Glucose Pump App → **Equipment**
2. Select the row for `SN-PRI-0007` (now available) in the **List View**.
3. Click **Actions** → **Scrap Device**

Expected system effects:
- Device is unlinked from any patient (if linked).
- Device is moved to the **Scrap location**.
- Patient chatter note (if previously linked): `Device SN SN-PRI-0007 scrapped`
- Equipment state becomes `Scrapped`.
- Dashboard card counts update (Scrapped increases).

## Final Verification Checklist (One Journey, All Features)

- **Index Page**: cards (Assigned/Unassigned/Scrapped), Devices/Patients navigation, columns, row click to Equipment.
- **Patients Index**: columns include primary/holiday devices, training location, consumables info, expiration/replacement/return dates.
- **Create Patient Modal**: contact info, device selectors, holiday return date validation, installation date, training location.
- **Equipment page**: Linked Patient Information tab, assignment type, installation/replacement dates, chatter enabled, state field.
- **Contacts Patients menu**: filtered patients, New Patient button, Patient Internal ID visible, patient-only fields/tab, company restriction.
- **Assignment logs**: primary + holiday creation, replacement date on old assignment, new log on replacement.
- **State transitions**: Available → Assigned → Available → Scrapped.
- **Replace Device Modal**: RMA-only selection, available-only replacement device, required chatter messages.
- **Unassign flow**: returns location transfer and chatter messages vary by assignment type.
- **Holiday pump request**: public form, case-insensitive serial validation, must be linked to a patient, helpdesk routing, email notification.
- **Consumables**: allocation per month, thresholds & indicators, warnings, no sales orders.
- **Alerts**: scheduled activity for devices within configured threshold, visible in Upcoming Activities.
- **Permissions**: Patient Administrators can access/edit everything above (including linked patient info on equipment).
