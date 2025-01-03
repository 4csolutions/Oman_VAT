import frappe
import os
import json
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import add_permission, update_permission_property


def setup(company=None, patch=True):

    add_permissions()
    make_custom_fields()


def add_permissions():
    """Add Permissions for OMAN VAT Setting."""
    add_permission("OMAN VAT Setting", "All", 0)
    for role in ("Accounts Manager", "Accounts User", "System Manager"):
        add_permission("OMAN VAT Setting", role, 0)
        update_permission_property("OMAN VAT Setting", role, 0, "write", 1)
        update_permission_property("OMAN VAT Setting", role, 0, "create", 1)

    """Enable OMAN VAT Report"""
    frappe.db.set_value("Report", "OMAN VAT", "disabled", 0)


def create_oman_vat_setting(company):
    """
    On creation of first company. Creates OMAN VAT Setting"""
    company = frappe.get_doc("Company", company)

    if frappe.db.exists("OMAN VAT Setting", company.name):
        return

    file_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "oman_vat_settings.json"
    )
    with open(file_path, "r") as json_file:
        account_data = json.load(json_file)

    # Creating OMAN VAT Setting
    oman_vat_setting = frappe.get_doc(
        {"doctype": "OMAN VAT Setting", "company": company.name}
    )

    for data in account_data:
        if data["type"] == "Sales Account":
            for row in data["accounts"]:
                item_tax_template = row["item_tax_template"]
                account = row["account"]
                oman_vat_setting.append(
                    "oman_vat_sales_accounts",
                    {
                        "title": row["title"],
                        "item_tax_template": f"{item_tax_template} - {company.abbr}",
                        "account": f"{account} - {company.abbr}",
                    },
                )

        elif data["type"] == "Purchase Account":
            for row in data["accounts"]:
                item_tax_template = row["item_tax_template"]
                account = row["account"]
                oman_vat_setting.append(
                    "oman_vat_purchase_accounts",
                    {
                        "title": row["title"],
                        "item_tax_template": f"{item_tax_template} - {company.abbr}",
                        "account": f"{account} - {company.abbr}",
                    },
                )

    oman_vat_setting.save()


def make_custom_fields():
    """Create Custom fields
    - QR code Image file
    - Company Name in Arabic
    - Address in Arabic
    """
    is_zero_rated = dict(
        fieldname="is_zero_rated",
        label="Is Zero Rated",
        fieldtype="Check",
        fetch_from="item_code.is_zero_rated",
        insert_after="description",
        print_hide=1,
    )

    is_exempt = dict(
        fieldname="is_exempt",
        label="Is Exempt",
        fieldtype="Check",
        fetch_from="item_code.is_exempt",
        insert_after="is_zero_rated",
        print_hide=1,
    )

    purchase_invoice_fields = [
        dict(
            fieldname="company_trn",
            label="Company TRN",
            fieldtype="Read Only",
            insert_after="shipping_address",
            fetch_from="company.tax_id",
            print_hide=1,
        ),
        dict(
            fieldname="supplier_name_in_arabic",
            label="Supplier Name in Arabic",
            fieldtype="Read Only",
            insert_after="supplier_name",
            fetch_from="supplier.supplier_name_in_arabic",
            print_hide=1,
        ),
    ]

    sales_invoice_fields = [
        dict(
            fieldname="company_trn",
            label="Company TRN",
            fieldtype="Read Only",
            insert_after="company_address",
            fetch_from="company.tax_id",
            print_hide=1,
        ),
        dict(
            fieldname="customer_name_in_arabic",
            label="Customer Name in Arabic",
            fieldtype="Read Only",
            insert_after="customer_name",
            fetch_from="customer.customer_name_in_arabic",
            print_hide=1,
        ),
        dict(
            fieldname="oman_einv_qr",
            label="OMAN E-Invoicing QR",
            fieldtype="Attach Image",
            read_only=1,
            no_copy=1,
            hidden=1,
        ),
    ]

    custom_fields = {
        "Item": [is_zero_rated, is_exempt],
        "Customer": [
            dict(
                fieldname="customer_name_in_arabic",
                label="Customer Name in Arabic",
                fieldtype="Data",
                insert_after="customer_name",
            ),
        ],
        "Supplier": [
            dict(
                fieldname="supplier_name_in_arabic",
                label="Supplier Name in Arabic",
                fieldtype="Data",
                insert_after="supplier_name",
            ),
        ],
        "Purchase Invoice": purchase_invoice_fields,
        "Purchase Order": purchase_invoice_fields,
        "Purchase Receipt": purchase_invoice_fields,
        "Sales Invoice": sales_invoice_fields,
        "POS Invoice": sales_invoice_fields,
        "Sales Order": sales_invoice_fields,
        "Delivery Note": sales_invoice_fields,
        "Sales Invoice Item": [is_zero_rated, is_exempt],
        "POS Invoice Item": [is_zero_rated, is_exempt],
        "Purchase Invoice Item": [is_zero_rated, is_exempt],
        "Sales Order Item": [is_zero_rated, is_exempt],
        "Delivery Note Item": [is_zero_rated, is_exempt],
        "Quotation Item": [is_zero_rated, is_exempt],
        "Purchase Order Item": [is_zero_rated, is_exempt],
        "Purchase Receipt Item": [is_zero_rated, is_exempt],
        "Supplier Quotation Item": [is_zero_rated, is_exempt],
        "Address": [
            dict(
                fieldname="address_in_arabic",
                label="Address in Arabic",
                fieldtype="Data",
                insert_after="address_line2",
            )
        ],
        "Company": [
            dict(
                fieldname="company_name_in_arabic",
                label="Company Name In Arabic",
                fieldtype="Data",
                insert_after="company_name",
            )
        ],
    }

    create_custom_fields(custom_fields, ignore_validate=True, update=True)


def create_company_settings(doc, method=None):
    update_regional_tax_settings(doc.country, doc.name)


def update_regional_tax_settings(country, company):
    if country == "Oman":
        create_oman_vat_setting(company)


def delete_vat_settings_for_company(doc, method=None):
    if doc.country == "Oman" and frappe.db.exists("OMAN VAT Setting", doc.name):
        frappe.delete_doc("OMAN VAT Setting", doc.name)
