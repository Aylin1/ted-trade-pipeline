import os

# Base Workspace Directory Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# Global Analytical Filters
START_DATE = "2018-01-01"
END_DATE = "2025-10-01"
IMPORT_COUNTRY = "DE"
MAX_FIRMS_PER_URL = 20

# Regulated Textile HS Tariff Codes used across notebooks
HS_CODES = [
    "610510", "610910", "611420", "621010", "621133", 
    "630231", "610610", "611300", "611510", "620630",
    "630260", "621142", "621143", "611610"
]
