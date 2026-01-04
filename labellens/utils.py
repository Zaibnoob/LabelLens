"""
Utility functions for LabelLens.

Common helper functions used across the application.
"""

import re
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def clean_ingredient_text(text: str) -> str:
    """
    Clean and normalize ingredient text from OCR or user input.
    
    Args:
        text: Raw ingredient text
        
    Returns:
        Cleaned text ready for analysis
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Fix common OCR errors
    ocr_fixes = {
        '0': 'O',  # Zero to O in context
        '|': 'I',  # Pipe to I
        '1': 'l',  # One to lowercase L in certain contexts
    }
    
    # Remove unwanted characters but keep ingredient-relevant punctuation
    text = re.sub(r'[^\w\s\-\(\)\,\;\.\%\/\&]', '', text)
    
    # Normalize multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def extract_percentage(text: str) -> Optional[float]:
    """
    Extract percentage value from ingredient text if present.
    
    Args:
        text: Ingredient text that may contain percentage
        
    Returns:
        Percentage as float (0-100) or None
    """
    match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def is_likely_allergen_warning(text: str) -> bool:
    """
    Check if text appears to be an allergen warning rather than ingredient.
    
    Args:
        text: Text to check
        
    Returns:
        True if this looks like an allergen warning
    """
    warning_patterns = [
        r'may contain',
        r'produced in a facility',
        r'processed in',
        r'made on.*equipment',
        r'contains:?\s*(milk|wheat|soy|eggs?|nuts?|peanuts?)',
        r'allergen',
        r'warning',
    ]
    
    text_lower = text.lower()
    for pattern in warning_patterns:
        if re.search(pattern, text_lower):
            return True
    return False


def categorize_ingredient(ingredient: str) -> str:
    """
    Categorize an ingredient into a general category.
    
    Args:
        ingredient: Single ingredient name
        
    Returns:
        Category string
    """
    ingredient_lower = ingredient.lower()
    
    categories = {
        'sweetener': ['sugar', 'syrup', 'sweetener', 'dextrose', 'fructose', 
                      'sucrose', 'honey', 'agave', 'stevia', 'aspartame'],
        'oil': ['oil', 'fat', 'butter', 'shortening', 'margarine', 'lard'],
        'protein': ['protein', 'whey', 'casein', 'collagen', 'gelatin'],
        'fiber': ['fiber', 'cellulose', 'inulin', 'pectin', 'psyllium'],
        'preservative': ['sorbate', 'benzoate', 'nitrate', 'nitrite', 
                        'sulfite', 'bht', 'bha', 'preservative'],
        'color': ['color', 'colour', 'dye', 'caramel color', 'red 40', 
                  'yellow 5', 'blue 1'],
        'flavor': ['flavor', 'flavour', 'vanilla', 'spice', 'extract'],
        'emulsifier': ['lecithin', 'mono and diglycerides', 'polysorbate'],
        'thickener': ['starch', 'gum', 'carrageenan', 'xanthan', 'guar'],
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in ingredient_lower:
                return category
    
    return 'other'


def format_profile_list(profiles: List[str], max_display: int = 3) -> str:
    """
    Format a list of profile names for display.
    
    Args:
        profiles: List of profile display names
        max_display: Maximum number to show before truncating
        
    Returns:
        Formatted string
    """
    if not profiles:
        return "None selected"
    
    if len(profiles) <= max_display:
        return ", ".join(profiles)
    
    shown = profiles[:max_display]
    remaining = len(profiles) - max_display
    return f"{', '.join(shown)} +{remaining} more"


def severity_to_score(severity: str) -> int:
    """
    Convert severity string to numeric score.
    
    Args:
        severity: Severity level string
        
    Returns:
        Numeric score (0-4)
    """
    scores = {
        'critical': 4,
        'high': 3,
        'medium': 2,
        'low': 1
    }
    return scores.get(severity.lower(), 0)


def calculate_overall_risk_score(risk_flags: List[dict]) -> float:
    """
    Calculate an overall risk score from individual risk flags.
    
    Args:
        risk_flags: List of risk flag dictionaries
        
    Returns:
        Risk score from 0.0 to 1.0
    """
    if not risk_flags:
        return 0.0
    
    total_score = sum(
        severity_to_score(flag.get('severity', 'low'))
        for flag in risk_flags
    )
    
    # Max possible score if all flags were critical
    max_possible = len(risk_flags) * 4
    
    return min(total_score / max_possible, 1.0)
