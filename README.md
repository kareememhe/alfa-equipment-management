# Alfa Equipment Management

A custom **Odoo 18** module that extends the standard Maintenance app for organisations that run medical and industrial equipment: hospitals, clinics and plants.

It answers four everyday questions:

- **When does this machine need calibrating?** Automatic calibration tracking with clear statuses.
- **Who reminds us?** A daily job that creates reminders for the responsible technician.
- **How does staff report a fault?** A QR code on every machine opens a bilingual (Arabic / English) report form on any phone, with no login needed.
- **Who approved this repair?** An approval workflow with a full audit trail.

> **The story in one line:** a machine breaks → a nurse scans its QR code → a request appears in Odoo → a manager approves → the technician repairs it → everything is recorded.

---

## Features

### Calibration tracking
- Calibration tab on every piece of equipment: requirement, interval (months), last calibration date.
- Next calibration date calculated automatically.
- Colour-coded status: **Valid**, **Due Soon** (within 30 days), **Overdue**, **Never Calibrated**.
- All calibration changes are logged in the equipment's history.

### Daily calibration alerts
- A scheduled action runs every day, refreshes every status (they depend on today's date) and creates a To-Do for the responsible technician.
- Covers equipment that needs calibration but has never been calibrated.
- Never creates duplicate reminders.

### QR fault reporting
- Each machine gets a unique, random QR token and a printable PDF label.
- Scanning opens a mobile-friendly public form in Arabic and English: name, description, priority.
- Staff can attach a photo of the problem (images only, up to 10 MB).
- Submitting creates a maintenance request linked to that machine, marked **Source: QR Code** with the reporter's name.
- Maintenance managers get an instant To-Do and inbox alert for every QR report, flagged when urgent.
- The random token means only people who physically scan a label can reach that machine's form.

### Approval workflow
- Requests move through **Draft → Waiting Approval → Approved / Rejected**.
- Only maintenance managers can approve or reject; this is checked on the server, not only by hiding buttons.
- A rejection requires a reason, which is posted to the request's history.
- A request cannot be closed as repaired unless it was approved, however someone tries to close it.
- Every approval step is tracked in the chatter: who, what and when.

### Dashboard
- **Calibration Overview:** pie chart of statuses and a list sorted by next calibration date.
- **Requests Analysis:** requests per machine by approval status, and QR reports compared with internal ones.

### Arabic
- Full Arabic translation of the module's interface, including buttons, statuses, dashboards and error messages, in right-to-left layout.

---

## Tech stack

- **Odoo 18** Community Edition (Python, PostgreSQL, XML views, QWeb templates)
- **PostgreSQL 16**
- **Docker** and **Docker Compose** for local development

---

## Project structure

```
alfa-equipment-management/
├── docker-compose.yml           # Odoo 18 + PostgreSQL 16
└── addons/
    ├── alfa_equipment/          # The main module
    │   ├── __manifest__.py
    │   ├── controllers/         # Public QR fault-report page
    │   ├── data/                # Daily scheduled action, upgrade hooks
    │   ├── i18n/ar.po           # Arabic translation
    │   ├── models/              # Equipment and request logic
    │   ├── report/              # Printable QR label (PDF)
    │   └── views/               # Forms, dashboard, QR page
    └── alfa_equipment_demo/     # Optional realistic sample data
```

---

## Running it locally

**Requirements:** Docker Desktop (on Windows, with WSL 2).

1. Clone the repository and start the containers:
   ```bash
   git clone https://github.com/kareememhe/alfa-equipment-management.git
   cd alfa-equipment-management
   docker compose up -d
   ```
2. Open http://localhost:8069 and create a database named `alfa_demo`. The compose file serves only that database name.
3. Turn on developer mode (Settings → bottom of the page).
4. Apps → **Update Apps List** → remove the "Apps" filter → search **Alfa**.
5. Install **Alfa Equipment Management**, or **Alfa Equipment Management - Demo Data** for a ready-made medical center and industrial plants. The demo module installs the main module automatically.

### Scanning QR codes from a phone
1. Find your computer's local IP address (`ipconfig` on Windows).
2. In Settings → Technical → System Parameters, set:
   - `web.base.url` = `http://YOUR-IP:8069`
   - `web.base.url.freeze` = `True`
   - `report.url` = `http://localhost:8069`
3. Connect the phone to the same network and scan any equipment's QR code.

---

## Design decisions

- **Extend, don't rebuild.** The module inherits Odoo's existing `maintenance.equipment` and `maintenance.request` models and views, so it stays compatible with standard Maintenance features and future updates.
- **Rules enforced on the server.** Manager-only actions and the "approve before closing" rule are checked in Python, not only hidden in the interface.
- **Audit trail by default.** Important fields use Odoo's tracking, so changes are logged without extra code.
- **Robust QR codes.** The QR keeps its white border, which phone cameras need, uses error correction for printed labels, and strips stray whitespace from the base URL setting.
- **Upgrade-safe.** Existing equipment gets QR tokens and refreshed calibration statuses automatically on every upgrade.
- **Demo data kept separate.** Sample data lives in its own module, so the main module stays clean for real use.

---

## Possible next steps

- Link spare parts to Odoo Inventory and track repair costs.
- SMS or WhatsApp notifications to technicians.
- Translate reminder titles into Arabic.
- Preventive maintenance plans per equipment category.

---

## Author

**Abdulkareem (Kareem) Arafa**, BSc (Hons) Computer Science, Nottingham Trent University
