# Odoo utils

`timesheet_preview.py` renders a preview of the current week in the terminal using the `curses` python package.

Requires the following environment variables:
* `USER`: must be the use to connect to Odoo
* `ODOO_PASSWORD`

Also the Odoo URL, database name and expected attendances must be set in the script manually.
