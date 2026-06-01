import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

TAXONOMY = [
    # ── Financial Services (FS) ─────────────────────────────────────────────
    ("Financial Services", "Retail Banking",       "Account Management"),
    ("Financial Services", "Retail Banking",       "Loans & Mortgages"),
    ("Financial Services", "Retail Banking",       "Payments & Transfers"),
    ("Financial Services", "Retail Banking",       "Customer Onboarding"),
    ("Financial Services", "Corporate Banking",    "Trade Finance"),
    ("Financial Services", "Corporate Banking",    "Treasury & Cash Management"),
    ("Financial Services", "Corporate Banking",    "Credit & Risk"),
    ("Financial Services", "Insurance",            "Policy Administration"),
    ("Financial Services", "Insurance",            "Claims Management"),
    ("Financial Services", "Insurance",            "Underwriting"),
    ("Financial Services", "Wealth Management",    "Portfolio Management"),
    ("Financial Services", "Wealth Management",    "Advisory & Planning"),
    # cross-cutting
    ("Financial Services", "Human Resources",      "Talent Acquisition"),
    ("Financial Services", "Human Resources",      "Learning & Development"),
    ("Financial Services", "Human Resources",      "Payroll & Benefits"),
    ("Financial Services", "Human Resources",      "Performance Management"),
    ("Financial Services", "Corporate",            "Legal & Compliance"),
    ("Financial Services", "Corporate",            "Finance & Accounting"),
    ("Financial Services", "Corporate",            "Procurement"),
    ("Financial Services", "Corporate",            "Risk Management"),
    ("Financial Services", "Data & Analytics",     "Data Engineering"),
    ("Financial Services", "Data & Analytics",     "BI & Reporting"),
    ("Financial Services", "Data & Analytics",     "AI & Machine Learning"),
    ("Financial Services", "Data & Analytics",     "Data Governance"),

    # ── Retail ──────────────────────────────────────────────────────────────
    ("Retail", "Merchandising",   "Pricing & Promotions"),
    ("Retail", "Merchandising",   "Category Management"),
    ("Retail", "Merchandising",   "Vendor Management"),
    ("Retail", "Supply Chain",    "Inventory Management"),
    ("Retail", "Supply Chain",    "Order Fulfilment"),
    ("Retail", "Supply Chain",    "Logistics & Distribution"),
    ("Retail", "Store Operations","Point of Sale"),
    ("Retail", "Store Operations","Loss Prevention"),
    ("Retail", "Store Operations","Staff Scheduling"),
    ("Retail", "eCommerce",       "Online Storefront"),
    ("Retail", "eCommerce",       "Customer Experience"),
    ("Retail", "eCommerce",       "Digital Marketing"),
    # cross-cutting
    ("Retail", "Human Resources", "Talent Acquisition"),
    ("Retail", "Human Resources", "Learning & Development"),
    ("Retail", "Human Resources", "Payroll & Benefits"),
    ("Retail", "Human Resources", "Performance Management"),
    ("Retail", "Corporate",       "Legal & Compliance"),
    ("Retail", "Corporate",       "Finance & Accounting"),
    ("Retail", "Corporate",       "Procurement"),
    ("Retail", "Corporate",       "Risk Management"),
    ("Retail", "Data & Analytics","Data Engineering"),
    ("Retail", "Data & Analytics","BI & Reporting"),
    ("Retail", "Data & Analytics","Customer Analytics"),
    ("Retail", "Data & Analytics","Data Governance"),

    # ── Consumer ────────────────────────────────────────────────────────────
    ("Consumer", "Marketing",          "Campaign Management"),
    ("Consumer", "Marketing",          "Brand Management"),
    ("Consumer", "Marketing",          "Customer Insights & Analytics"),
    ("Consumer", "Customer Service",   "Contact Centre"),
    ("Consumer", "Customer Service",   "Complaints & Resolution"),
    ("Consumer", "Customer Service",   "Self-Service"),
    ("Consumer", "Product Development","Product Lifecycle Management"),
    ("Consumer", "Product Development","R&D & Innovation"),
    ("Consumer", "Sales",              "Channel Management"),
    ("Consumer", "Sales",              "Trade Promotions"),
    ("Consumer", "Sales",              "Key Account Management"),
    # cross-cutting
    ("Consumer", "Human Resources",    "Talent Acquisition"),
    ("Consumer", "Human Resources",    "Learning & Development"),
    ("Consumer", "Human Resources",    "Payroll & Benefits"),
    ("Consumer", "Human Resources",    "Performance Management"),
    ("Consumer", "Corporate",          "Legal & Compliance"),
    ("Consumer", "Corporate",          "Finance & Accounting"),
    ("Consumer", "Corporate",          "Procurement"),
    ("Consumer", "Corporate",          "Risk Management"),
    ("Consumer", "Data & Analytics",   "Data Engineering"),
    ("Consumer", "Data & Analytics",   "BI & Reporting"),
    ("Consumer", "Data & Analytics",   "Customer Analytics"),
    ("Consumer", "Data & Analytics",   "Data Governance"),

    # ── Technology ──────────────────────────────────────────────────────────
    ("Technology", "IT Operations",        "Service Desk"),
    ("Technology", "IT Operations",        "Infrastructure Management"),
    ("Technology", "IT Operations",        "Monitoring & Alerting"),
    ("Technology", "Software Development", "SDLC & Agile Delivery"),
    ("Technology", "Software Development", "DevOps & CI/CD"),
    ("Technology", "Software Development", "QA & Testing"),
    ("Technology", "Cybersecurity",        "Identity & Access Management"),
    ("Technology", "Cybersecurity",        "Threat Detection & Response"),
    ("Technology", "Cybersecurity",        "Vulnerability Management"),
    # cross-cutting
    ("Technology", "Human Resources",      "Talent Acquisition"),
    ("Technology", "Human Resources",      "Learning & Development"),
    ("Technology", "Human Resources",      "Payroll & Benefits"),
    ("Technology", "Human Resources",      "Performance Management"),
    ("Technology", "Corporate",            "Legal & Compliance"),
    ("Technology", "Corporate",            "Finance & Accounting"),
    ("Technology", "Corporate",            "Procurement"),
    ("Technology", "Corporate",            "Risk Management"),
    ("Technology", "Data & Analytics",     "Data Engineering"),
    ("Technology", "Data & Analytics",     "BI & Reporting"),
    ("Technology", "Data & Analytics",     "AI & Machine Learning"),
    ("Technology", "Data & Analytics",     "Data Governance"),

    # ── Healthcare ──────────────────────────────────────────────────────────
    ("Healthcare", "Clinical Operations", "Patient Management"),
    ("Healthcare", "Clinical Operations", "Clinical Workflow"),
    ("Healthcare", "Finance & Admin",     "Billing & Coding"),
    ("Healthcare", "Finance & Admin",     "Compliance & Regulatory"),
    ("Healthcare", "Pharmacy",            "Supply & Dispensing"),
    # cross-cutting
    ("Healthcare", "Human Resources",     "Talent Acquisition"),
    ("Healthcare", "Human Resources",     "Learning & Development"),
    ("Healthcare", "Human Resources",     "Payroll & Benefits"),
    ("Healthcare", "Human Resources",     "Performance Management"),
    ("Healthcare", "Corporate",           "Legal & Compliance"),
    ("Healthcare", "Corporate",           "Finance & Accounting"),
    ("Healthcare", "Corporate",           "Procurement"),
    ("Healthcare", "Data & Analytics",    "Data Engineering"),
    ("Healthcare", "Data & Analytics",    "BI & Reporting"),
    ("Healthcare", "Data & Analytics",    "Clinical Analytics"),

    # ── Manufacturing ───────────────────────────────────────────────────────
    ("Manufacturing", "Production",     "Planning & Scheduling"),
    ("Manufacturing", "Production",     "Quality Control"),
    ("Manufacturing", "Supply Chain",   "Procurement"),
    ("Manufacturing", "Supply Chain",   "Warehouse Management"),
    ("Manufacturing", "Engineering",    "Maintenance & Asset Management"),
    ("Manufacturing", "Engineering",    "Product Design & Engineering"),
    # cross-cutting
    ("Manufacturing", "Human Resources","Talent Acquisition"),
    ("Manufacturing", "Human Resources","Learning & Development"),
    ("Manufacturing", "Human Resources","Payroll & Benefits"),
    ("Manufacturing", "Human Resources","Performance Management"),
    ("Manufacturing", "Corporate",      "Legal & Compliance"),
    ("Manufacturing", "Corporate",      "Finance & Accounting"),
    ("Manufacturing", "Corporate",      "Risk Management"),
    ("Manufacturing", "Data & Analytics","Data Engineering"),
    ("Manufacturing", "Data & Analytics","BI & Reporting"),
    ("Manufacturing", "Data & Analytics","Operational Analytics"),
]

def seed():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    # Drop application_name from taxonomy if it exists (not needed - it's free text on documents)
    cur.execute("""
        ALTER TABLE taxonomy DROP COLUMN IF EXISTS application_name;
    """)

    # Clear existing taxonomy rows to avoid duplication on re-runs
    cur.execute("TRUNCATE TABLE taxonomy RESTART IDENTITY;")

    # Insert all taxonomy entries
    for bu, area, func in TAXONOMY:
        cur.execute("""
            INSERT INTO taxonomy (business_unit, business_area, business_function)
            VALUES (%s, %s, %s)
        """, (bu, area, func))

    # Update the existing document to Retail / Merchandising / Vendor Management
    cur.execute("""
        UPDATE documents
        SET business_unit = 'Retail',
            business_area = 'Merchandising',
            business_function = 'Vendor Management'
        WHERE business_unit IS NULL OR business_unit = '';
    """)

    updated = cur.rowcount
    conn.commit()

    # Summary
    cur.execute("SELECT COUNT(*) FROM taxonomy;")
    count = cur.fetchone()[0]
    cur.execute("SELECT id, name, business_unit, business_area, business_function FROM documents;")
    docs = cur.fetchall()

    cur.close()
    conn.close()

    print(f"✅ Taxonomy seeded: {count} rows")
    print(f"✅ Documents updated: {updated} row(s)")
    print("\nDocuments in DB:")
    for d in docs:
        print(f"  [{d[0]}] {d[1]} → {d[2]} / {d[3]} / {d[4]}")

if __name__ == "__main__":
    seed()
