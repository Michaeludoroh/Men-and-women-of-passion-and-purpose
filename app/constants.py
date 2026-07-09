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
    "offering": {
        "label": "Offering",
        "description": "A freewill gift to support the ministry's work and outreach.",
        "scripture": "2 Corinthians 9:7",
    },
    "thanksgiving": {
        "label": "Thanksgiving Offering",
        "description": "Express gratitude to God for His faithfulness and blessings.",
        "scripture": "Psalm 107:1",
    },
    "general_offering": {
        "label": "General Offering",
        "description": "Support general ministry operations and kingdom advancement.",
        "scripture": "Malachi 3:10",
    },
    "tithe": {
        "label": "Tithe",
        "description": "Honor God with the first tenth of your increase.",
        "scripture": "Proverbs 3:9-10",
    },
    "seeds": {
        "label": "Seeds",
        "description": "Sow a seed of faith into the ministry and watch God multiply it.",
        "scripture": "Luke 6:38",
    },
    "father_seed": {
        "label": "Father Seed",
        "description": "Honor and support the father of the house through a special seed.",
        "scripture": "1 Timothy 5:17",
    },
    "charity_seed": {
        "label": "Charity Seed",
        "description": "Give to support the needy and charitable outreach programs.",
        "scripture": "Proverbs 19:17",
    },
    "five_fold": {
        "label": "Five-Fold Ministry Giving",
        "description": "Support the five-fold ministry — apostles, prophets, evangelists, pastors, and teachers.",
        "scripture": "Ephesians 4:11-12",
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
