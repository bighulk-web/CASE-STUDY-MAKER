"""Keyword dictionaries used by the deterministic heuristic extractor and by the
prompt intent parser. Values map canonical labels -> trigger phrases (lowercased)."""

from __future__ import annotations

INDUSTRIES: dict[str, list[str]] = {
    "Manufacturing": ["manufacturing", "factory", "industrial", "production plant", "assembly"],
    "Healthcare": ["healthcare", "hospital", "clinical", "patient", "pharma", "medical", "life sciences"],
    "BFSI": ["bank", "banking", "financial services", "insurance", "bfsi", "fintech", "capital markets"],
    "Government": ["government", "public sector", "ministry", "municipal", "federal", "citizen services"],
    "Retail": ["retail", "e-commerce", "ecommerce", "consumer goods", "cpg", "point of sale"],
    "Automotive": ["automotive", "vehicle", "car manufacturer", "oem", "mobility"],
    "Energy": ["energy", "oil and gas", "utilities", "power grid", "renewable"],
    "Telecom": ["telecom", "telecommunications", "5g", "network operator", "carrier"],
    "Technology": ["software company", "saas", "technology firm", "high tech"],
    "Logistics": ["logistics", "supply chain", "transportation", "freight", "warehouse"],
    "Education": ["education", "university", "school", "edtech", "learning"],
}

TECHNOLOGIES: dict[str, list[str]] = {
    "SAP S/4HANA": ["s/4hana", "s4hana", "s/4 hana"],
    "SAP": ["sap "],
    "Oracle ERP": ["oracle erp", "oracle fusion", "oracle e-business"],
    "Oracle": ["oracle "],
    "Microsoft Azure": ["azure"],
    "AWS": ["aws", "amazon web services"],
    "Google Cloud": ["gcp", "google cloud"],
    "Salesforce": ["salesforce"],
    "ServiceNow": ["servicenow"],
    "Workday": ["workday"],
    "Artificial Intelligence": ["artificial intelligence", " ai ", "ai-", "machine learning", "ml ", "genai", "llm", "generative ai"],
    "Data Analytics": ["analytics", "data warehouse", "business intelligence", "power bi", "tableau"],
    "IoT": ["iot", "internet of things", "sensors"],
    "RPA": ["rpa", "robotic process automation", "uipath", "automation anywhere"],
    "Cloud Migration": ["cloud migration", "lift and shift", "re-platform"],
    "Cybersecurity": ["cybersecurity", "security operations", "zero trust"],
    "Kubernetes": ["kubernetes", "k8s", "containerization"],
}

REGIONS: dict[str, list[str]] = {
    "EMEA": ["emea", "europe", "middle east", "africa", "uk", "germany", "france"],
    "North America": ["north america", "usa", "united states", "canada", "u.s."],
    "APAC": ["apac", "asia pacific", "asia-pacific", "australia", "singapore", "japan", "china"],
    "India": ["india", "bengaluru", "mumbai", "delhi"],
    "LATAM": ["latam", "latin america", "brazil", "mexico"],
    "Global": ["global", "worldwide", "multinational"],
}

BUSINESS_FUNCTIONS: dict[str, list[str]] = {
    "Finance": ["finance", "accounting", "financial close", "treasury"],
    "Supply Chain": ["supply chain", "procurement", "inventory", "logistics"],
    "Human Resources": ["human resources", "hr ", "payroll", "talent"],
    "Sales": ["sales", "crm", "revenue"],
    "Marketing": ["marketing", "campaign", "customer engagement"],
    "Operations": ["operations", "manufacturing operations", "plant"],
    "IT": ["it modernization", "infrastructure", "devops", "platform"],
    "Customer Service": ["customer service", "contact center", "support"],
}

STOPWORDS = set(
    """a an the and or but if then else of to in on for with without within into over under
    is are was were be been being this that these those it its as at by from we our their they
    them he she his her you your i me my will would can could should may might must not no yes
    which who whom whose what when where why how than so such very more most much many few
    also using used use case study customer client project solution challenge business
    company organization team across enabled delivered implemented deployed""".split()
)
