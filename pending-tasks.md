# Pending Tasks & Issues

## Functional Issues
- [x] **Website Holiday Pump Request Form (404 Error)**: Implemented controller and template. Verified form submission creates `glucose.holiday.pump.request`.
- [x] **Assignment History Tab on Patient Form**: Added "Assignment History" and "Consumables" tabs to the `res.partner` form.

## Omissions
- [x] **Return Location Logic**: Verified that the "Replace Device" wizard correctly transfers the old device to the configured return location via stock moves.
- [x] **Activity Cleanup**: Implemented automated cleanup of "Replacement date approaching" activities when a device is unassigned or replaced.

## Completed Testing
- [x] Patient Creation & Internal ID Generation
- [x] Primary & Holiday Pump Assignment
- [x] Consumables Allocation & Threshold Badge Logic
- [x] Replacement Date Alert (Cron & Activity Creation)
- [x] Unassign Workflow
- [x] RMA Replacement Wizard (Restricted to RMA products)
- [x] Scrap Device Workflow
- [x] Website Form Submission & Validation
- [x] Duplicate Assignment Log Prevention
