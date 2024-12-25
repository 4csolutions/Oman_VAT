import json
import os, frappe

from erpnext.setup.setup_wizard.operations.taxes_setup import (
    from_detailed_data
)


def setup_templates(doc, method=None):
    if doc.country == "Oman":
        file_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "oman_template.json"
        )
        default_taxes = frappe.get_file_json(file_path)
        from_detailed_data(doc.name, default_taxes)
