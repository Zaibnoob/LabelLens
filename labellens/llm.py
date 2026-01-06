"""
Groq LLM Integration Layer for LabelLens.

Handles all interactions with Groq API using Llama models,
including prompt construction, response parsing, and error handling.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import GROQ_API_KEY, GROQ_MODEL, MAX_RETRIES, RETRY_DELAY, Verdict
from .profiles import UserProfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GroqClient:
    """
    Client for interacting with Groq API.
    
    Handles API configuration, prompt construction, and response parsing
    with built-in retry logic and error handling.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Groq client.
        
        Args:
            api_key: Optional API key (falls back to environment variable)
        """
        self.api_key = api_key or GROQ_API_KEY
        if not self.api_key:
            raise ValueError(
                "Groq API key not found. Set GROQ_API_KEY environment variable "
                "or pass api_key to GroqClient."
            )
        
        self.client = Groq(api_key=self.api_key)
        self.model = GROQ_MODEL
    
    def _build_system_prompt(self, user_profile: UserProfile) -> str:
        """
        Build a context-aware system prompt based on user's health profile.
        """
        profile_names = ", ".join(user_profile.get_display_names())
        combined_context = user_profile.get_combined_context()
        severity_note = ""
        
        if user_profile.has_high_severity_profile():
            severity_note = """
⚠️ SAFETY CRITICAL: This user has conditions where certain ingredients 
could cause severe allergic reactions or immediate health emergencies.
Err on the side of extreme caution for these profiles.
"""
        
        return f"""You are an expert clinical nutritionist and food scientist specializing in personalized dietary analysis for patients with the following conditions:

**Active Health Profiles:** {profile_names}

{combined_context}

{severity_note}

YOUR TASK:
Analyze ingredient lists from food products and identify risks SPECIFIC to this patient's health profiles.

CRITICAL INSTRUCTIONS:
1. Focus ONLY on risks relevant to the specified health profiles
2. Flag hidden ingredients that might not be obvious (e.g., "natural flavors" hiding garlic for IBS)
3. Identify deceptive marketing terms (e.g., "no added sugar" but contains maltodextrin)
4. Consider ingredient order (first ingredients are most prevalent)
5. Handle uncertainty explicitly - if "natural flavors" or "spices" could contain problematic ingredients, flag with probability
6. Provide smart swap suggestions that are SAFE for all active profiles

IMPORTANT CONSTRAINTS:
- Do NOT provide medical advice
- Use evidence-based reasoning only
- Explain risks in simple, grocery-aisle-friendly language
- When uncertain, lean toward caution but acknowledge uncertainty

OUTPUT FORMAT:
You MUST respond with valid JSON only, no additional text or markdown code blocks.
"""

    def _build_analysis_prompt(self, ingredients: str) -> str:
        """
        Build the analysis prompt for ingredient evaluation.
        """
        return f"""Analyze the following ingredient list for this patient:

INGREDIENTS:
{ingredients}

Respond with a JSON object in EXACTLY this format (no markdown, just raw JSON):
{{
    "overall_verdict": "SAFE" or "CAUTION" or "AVOID",
    "confidence_score": 0.0 to 1.0,
    "risk_flags": [
        {{
            "ingredient": "exact ingredient name from list",
            "risk_type": "hidden_sugar|allergen|metabolic_conflict|high_sodium|high_fodmap|contains_gluten|high_glycemic|seed_oil|high_protein|not_keto_friendly|uncertainty|deceptive_marketing",
            "severity": "low|medium|high|critical",
            "explanation": "Brief, clear explanation of why this is problematic for this patient",
            "relevant_profiles": ["list of affected profile names"]
        }}
    ],
    "deception_alerts": [
        {{
            "claim": "marketing claim or misleading term",
            "reality": "what it actually means",
            "concern_level": "low|medium|high"
        }}
    ],
    "uncertainty_flags": [
        {{
            "ingredient": "ambiguous ingredient like 'natural flavors'",
            "possible_concerns": ["list of possible hidden ingredients"],
            "recommendation": "brief recommendation"
        }}
    ],
    "safe_for_general_public": true or false,
    "user_specific_warning": true or false,
    "smart_swaps": [
        {{
            "avoid": "problematic ingredient or product type",
            "try_instead": "safer alternative",
            "reason": "why this swap works for this patient"
        }}
    ],
    "summary": "2-3 sentence plain-English summary for the user"
}}

Remember: Respond ONLY with the JSON object, no markdown formatting or code blocks."""

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=RETRY_DELAY, min=1, max=10),
        retry=retry_if_exception_type((json.JSONDecodeError, ValueError))
    )
    def _call_groq(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Make a call to Groq API with retry logic.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Handle potential markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise
    
    def analyze_ingredients(
        self, 
        ingredients: str, 
        user_profile: UserProfile
    ) -> Dict[str, Any]:
        """
        Analyze ingredients against a user's health profile.
        
        This is the main entry point for ingredient analysis.
        """
        if not ingredients or not ingredients.strip():
            return self._empty_result("No ingredients provided")
        
        if not user_profile.active_profiles:
            return self._empty_result("No health profiles selected")
        
        system_prompt = self._build_system_prompt(user_profile)
        analysis_prompt = self._build_analysis_prompt(ingredients)
        
        try:
            result = self._call_groq(system_prompt, analysis_prompt)
            return self._validate_and_normalize(result)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._error_result(str(e))
    
    def detect_semantic_deception(
        self, 
        ingredients: str,
        product_claims: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect deceptive marketing or misleading ingredient labeling.
        """
        claims_text = ""
        if product_claims:
            claims_text = f"\n\nMARKETING CLAIMS ON PACKAGE:\n" + "\n".join(f"- {c}" for c in product_claims)
        
        system_prompt = """You are a food labeling expert detecting deceptive marketing practices.
Analyze ingredient lists for semantic deception - cases where the labeling is technically legal but misleading to consumers.
Respond with valid JSON only."""

        user_prompt = f"""Analyze this ingredient list for semantic deception:

INGREDIENTS:
{ingredients}
{claims_text}

Look for:
1. Sugar disguised under alternative names
2. "No added sugar" products with high-glycemic ingredients
3. "Natural" claims on highly processed ingredients
4. Serving size manipulation
5. Health halos (implying benefits not supported by ingredients)
6. Allergen obfuscation
7. "Clean label" ingredients that aren't actually healthier

Respond with JSON only:
{{
    "deception_detected": true or false,
    "deception_score": 0.0 to 1.0,
    "findings": [
        {{
            "type": "category of deception",
            "evidence": "specific ingredient or claim",
            "explanation": "why this is deceptive",
            "severity": "low|medium|high"
        }}
    ],
    "overall_assessment": "brief summary"
}}
"""
        
        try:
            result = self._call_groq(system_prompt, user_prompt)
            return result
        except Exception as e:
            logger.error(f"Deception detection failed: {e}")
            return {
                "deception_detected": False,
                "deception_score": 0.0,
                "findings": [],
                "overall_assessment": f"Analysis failed: {e}",
                "error": True
            }
    
    def _validate_and_normalize(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize the analysis result.
        """
        normalized = {
            "overall_verdict": result.get("overall_verdict", Verdict.CAUTION),
            "confidence_score": result.get("confidence_score", 0.5),
            "risk_flags": result.get("risk_flags", []),
            "deception_alerts": result.get("deception_alerts", []),
            "uncertainty_flags": result.get("uncertainty_flags", []),
            "safe_for_general_public": result.get("safe_for_general_public", True),
            "user_specific_warning": result.get("user_specific_warning", False),
            "smart_swaps": result.get("smart_swaps", []),
            "summary": result.get("summary", "Analysis complete."),
            "error": False
        }
        
        if normalized["overall_verdict"] not in [Verdict.SAFE, Verdict.CAUTION, Verdict.AVOID]:
            normalized["overall_verdict"] = Verdict.CAUTION
        
        return normalized
    
    def _empty_result(self, message: str) -> Dict[str, Any]:
        """Return an empty result with a message."""
        return {
            "overall_verdict": Verdict.CAUTION,
            "confidence_score": 0.0,
            "risk_flags": [],
            "deception_alerts": [],
            "uncertainty_flags": [],
            "safe_for_general_public": True,
            "user_specific_warning": False,
            "smart_swaps": [],
            "summary": message,
            "error": True
        }
    
    def _error_result(self, error_message: str) -> Dict[str, Any]:
        """Return an error result."""
        return {
            "overall_verdict": Verdict.CAUTION,
            "confidence_score": 0.0,
            "risk_flags": [],
            "deception_alerts": [],
            "uncertainty_flags": [],
            "safe_for_general_public": True,
            "user_specific_warning": False,
            "smart_swaps": [],
            "summary": f"Analysis failed: {error_message}",
            "error": True,
            "error_message": error_message
        }


# Convenience function for module-level access
_client: Optional[GroqClient] = None

def get_client(api_key: Optional[str] = None) -> GroqClient:
    """
    Get or create a singleton GroqClient instance.
    """
    global _client
    if _client is None:
        _client = GroqClient(api_key)
    return _client


# OCR reader singleton (lazy loaded)
_ocr_reader = None
_ocr_type = None  # 'tesseract' or 'easyocr'

def _get_ocr_reader():
    """Get or create the OCR reader (lazy loaded for performance). Tries pytesseract first (lighter), falls back to easyocr."""
    global _ocr_reader, _ocr_type
    
    if _ocr_reader is not None:
        return _ocr_reader, _ocr_type
    
    # Try pytesseract first (lighter, faster to deploy)
    try:
        import pytesseract
        _ocr_reader = pytesseract
        _ocr_type = 'tesseract'
        logger.info("Using pytesseract for OCR")
        return _ocr_reader, _ocr_type
    except ImportError:
        pass
    
    # Fall back to easyocr
    try:
        import easyocr
        _ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        _ocr_type = 'easyocr'
        logger.info("Using easyocr for OCR")
        return _ocr_reader, _ocr_type
    except ImportError:
        pass
    
    return None, None


def extract_ingredients_from_image(image_bytes: bytes, api_key: Optional[str] = None) -> Optional[str]:
    """
    Extract ingredient text from an image using available OCR.
    
    Tries pytesseract first (lighter), falls back to easyocr.
    
    Args:
        image_bytes: Raw image bytes from camera or file upload
        api_key: Not used (kept for API compatibility)
        
    Returns:
        Extracted ingredient text or None if extraction fails
    """
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        import io
        
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize large images for faster processing
        max_dimension = 1200
        if max(image.size) > max_dimension:
            ratio = max_dimension / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.LANCZOS)
        
        # Convert to grayscale for better OCR
        gray_image = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(gray_image)
        gray_image = enhancer.enhance(1.5)
        
        # Sharpen
        gray_image = gray_image.filter(ImageFilter.SHARPEN)
        
        # Get OCR reader
        reader, ocr_type = _get_ocr_reader()
        
        if reader is None:
            logger.error("No OCR engine available")
            return None
        
        if ocr_type == 'tesseract':
            # Use pytesseract
            full_text = reader.image_to_string(gray_image)
        else:
            # Use easyocr
            import numpy as np
            processed_image = gray_image.convert('RGB')
            img_array = np.array(processed_image)
            
            results = reader.readtext(
                img_array,
                detail=1,
                paragraph=False,
                min_size=10,
                text_threshold=0.6,
                low_text=0.3,
                width_ths=0.5,
                batch_size=8
            )
            
            if not results:
                return None
            
            extracted_lines = [text for (bbox, text, conf) in results if conf > 0.25]
            full_text = ' '.join(extracted_lines)
        
        if not full_text or not full_text.strip():
            logger.warning("No text detected in image")
            return None
        
        # Clean up common OCR issues
        full_text = full_text.replace('|', 'l')
        
        logger.info(f"Successfully extracted text from image using {ocr_type}")
        return full_text.strip()
        
    except ImportError as e:
        logger.error(f"OCR dependencies not installed: {e}")
        return None
    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
        return None
