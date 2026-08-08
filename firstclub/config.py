"""Configuration for FirstClub install-to-first-order funnel analysis."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Synthetic dataset scale (representative of 1.2M+ order production warehouse)
ORDER_COUNT = 1_200_000
RANDOM_SEED = 42

# Funnel stages (install → first order)
FUNNEL_STAGES = [
    "install",
    "signup",
    "location_set",
    "catalog_view",
    "cart_add",
    "checkout_start",
    "payment_success",
    "first_order_delivered",
]

# Cities for launch playbook
CITIES = ["Bangalore", "Mumbai", "Delhi NCR", "Hyderabad", "Pune", "Chennai"]

# Competitive set (quick-commerce India)
COMPETITORS = ["Blinkit", "Zepto", "Swiggy Instamart", "BigBasket Now", "FirstClub"]

# Unit economics defaults (INR)
DEFAULT_AOV = 485.0
DEFAULT_CAC = 185.0
DEFAULT_GROSS_MARGIN = 0.22
DEFAULT_MONTHLY_CHURN = 0.38
DEFAULT_ORDERS_PER_ACTIVE_MONTH = 2.4

# CAC/LTV simulator scale
SIMULATOR_ORDER_SCALE = 1_000_000
