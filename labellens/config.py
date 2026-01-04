"""
Configuration settings for LabelLens.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"  # Fast and capable model

# Analysis Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds

# Verdicts
class Verdict:
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    AVOID = "AVOID"

# Risk Types
class RiskType:
    HIDDEN_SUGAR = "hidden_sugar"
    ALLERGEN = "allergen"
    METABOLIC_CONFLICT = "metabolic_conflict"
    HIGH_SODIUM = "high_sodium"
    HIGH_FODMAP = "high_fodmap"
    CONTAINS_GLUTEN = "contains_gluten"
    HIGH_GLYCEMIC = "high_glycemic"
    SEED_OIL = "seed_oil"
    HIGH_PROTEIN = "high_protein"
    NOT_KETO_FRIENDLY = "not_keto_friendly"
    UNCERTAINTY = "uncertainty"
    DECEPTIVE_MARKETING = "deceptive_marketing"
