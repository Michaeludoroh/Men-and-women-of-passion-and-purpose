"""Shared ministry constants for forms, giving, and partnerships."""

PRAYER_CATEGORIES = [
    ("healing", "Healing & Health"),
    ("family", "Family & Relationships"),
    ("financial", "Financial Breakthrough"),
    ("spiritual", "Spiritual Growth"),
    ("salvation", "Salvation & Deliverance"),
    ("career", "Career & Purpose"),
    ("other", "Other"),
]

CURRENCIES = [
    ("NGN", "Nigerian Naira (₦)"),
    ("USD", "US Dollar ($)"),
    ("GBP", "British Pound (£)"),
    ("EUR", "Euro (€)"),
]

CURRENCY_SYMBOLS = {"NGN": "₦", "USD": "$", "GBP": "£", "EUR": "€"}

PAYMENT_METHODS = [
    ("flutterwave", "Flutterwave (Naira)"),
    ("paystack", "Paystack"),
    ("paypal", "PayPal"),
    ("zelle", "Zelle"),
    ("cashapp", "Cash App"),
]

GIVING_CATEGORIES = {
    "tithing": {
        "label": "Tithing",
        "description": "Faithfully honour God with the first fruits of your increase in obedience and worship.",
        "icon": "fa-hand-holding-heart",
    },
    "general_offering": {
        "label": "General Offering",
        "description": "Support the ongoing work of the ministry and help advance the Gospel.",
        "icon": "fa-church",
    },
    "general_thanksgiving": {
        "label": "General Thanksgiving",
        "description": "Express gratitude to God for His faithfulness and abundant blessings.",
        "icon": "fa-praying-hands",
    },
    "prophetic_seed": {
        "label": "Prophetic Seed",
        "description": "Sow in faith as the Lord leads, believing Him for spiritual growth and divine direction.",
        "icon": "fa-seedling",
    },
    "charity_seed": {
        "label": "Charity Seed",
        "description": "Support outreach programmes, welfare initiatives, and practical assistance for those in need.",
        "icon": "fa-hands-helping",
    },
}

PARTNERSHIP_FREQUENCIES = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("biweekly", "Biweekly"),
    ("monthly", "Monthly"),
    ("semi_monthly", "Semi-Monthly"),
    ("quarterly", "Quarterly"),
    ("annually", "Annually"),
]

ORG_LEVELS = [
    ("founder", "Founder"),
    ("executive", "Executive Leadership"),
    ("pastoral", "Pastoral Leadership"),
    ("director", "Ministry Directors"),
    ("department_head", "Department Heads"),
    ("coordinator", "Coordinators"),
    ("volunteer", "Volunteers"),
]

ORG_LEVEL_ORDER = {level: idx for idx, (level, _) in enumerate(ORG_LEVELS)}

PAYMENT_STATUS_PENDING = "pending"
PAYMENT_STATUS_VERIFIED = "verified"
PAYMENT_STATUS_FAILED = "failed"
PAYMENT_STATUS_MANUAL = "manual"

PARTNERSHIP_STATUS_ACTIVE = "active"
PARTNERSHIP_STATUS_PAUSED = "paused"
PARTNERSHIP_STATUS_CANCELLED = "cancelled"
