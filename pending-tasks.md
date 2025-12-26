# Pending Tasks - Glucose Pumps Addon

This document lists the functionality missing or incorrect in the current implementation of the Glucose Pumps addon compared to the `spec.md`.

## A. New Pages & UI Components

### 1. Glucose Pumps Index Page (Dashboard)
- [x] **Header Cards**: Missing cards displaying counts for Assigned, Unassigned, and Scrapped devices. (Implemented via Kanban dashboard view)
- [x] **Default View**: The module should default to the "Devices" (Equipment) view, but currently defaults to "Patients".
- [x] **Columns**: Missing "Upcoming Activities" and "Installation Date" columns in the list view.
- [x] **Actions**: Missing "Unassign Device", "Replace Device", and "Scrap Device" options in the list view's Action button.


### 2. Patient Management
- [x] **Create Patient Button**: The "New" button should be renamed to "New Patient".
- [x] **Patient Form Fields**:
    - [x] Missing "Holiday Pump Return Date" (mandatory when holiday pump is assigned).
    - [x] Missing "Installation Date" (default today, editable).
- [x] **Card View**: Patient Internal ID should be displayed on the card view.

### 3. Equipment Management
- [x] **Linked Patient Information Tab**: Missing from the Equipment (Stock Lot) form.
- [x] **Pump State Field**: Should be a selection field (Available, Assigned, Scrapped) instead of just a badge.
- [x] **Chatter**: Enable chatter on Equipment records.

### 4. Replace Device Workflow
- [x] **Replace Device Modal**: Entirely missing.
- [x] **Replacement Logic**: Logic for unlinking old device, transferring to return location, and assigning RMA device is missing.
- [x] **Validation**: RMA device constraints (only RMA products for replacement, etc.) are missing.

### 5. Holiday Pump Request Form
- [ ] **Public Website Form**: Missing (no controllers or website views implemented).
- [ ] **Validation**: Serial number existence and attachment validation on the form is missing.
- [ ] **Helpdesk Integration**: Integration with a new Holiday Pump Helpdesk is missing.

### 6. Consumables Tracking
- [ ] **Menu Location**: Should be located directly under "Glucose Pump App" or as a top-level menu, not under "Operations".
- [ ] **Threshold Warnings**: Verify if "Charge for additional pumps" warning is implemented for >13 consumables.

### 7. Settings Page
- [ ] **Menu Item**: Missing from the Configuration menu.
- [ ] **Configuration Options**: UI for configuring RMA products, return locations, alert thresholds, and helpdesk email is missing.

## B. Backend & Logic

### 1. Automated Actions
- [ ] **Replacement Date Alerts**: Missing daily scheduled action to check for devices approaching replacement date and create activities.

### 2. Constraints & Validations
- [ ] **RMA Device Constraints**: System should prevent assignment of RMA devices outside of the replacement workflow.
- [ ] **Patient Internal ID**: Verify if the sequence resets annually as per "YYYY-NNN" format.

### 3. Permissions
- [ ] **Patient Administrators Group**: Verify if the group has the correct access rights and if demo users (Jonathan, Denise) are correctly assigned.
