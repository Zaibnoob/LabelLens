"""
Core Analysis Engine for LabelLens.

This module provides the main analysis functions that orchestrate
the ingredient analysis pipeline, combining LLM reasoning with
rule-based validation.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import re
import logging

from .profiles import UserProfile, ProfileType, HEALTH_PROFILES
from .llm import GroqClient, get_client
from .config import Verdict, RiskType

logger = logging.getLogger(__name__)


@dataclass
class RiskFlag:
    """Represents a single risk flag for an ingredient."""
    ingredient: str
    risk_type: str
    severity: str
    explanation: str
    relevant_profiles: List[str]


@dataclass
class DeceptionAlert:
    """Represents a deceptive marketing finding."""
    claim: str
    reality: str
    concern_level: str


@dataclass
class SmartSwap:
    """Represents a safer alternative suggestion."""
    avoid: str
    try_instead: str
    reason: str


@dataclass
class AnalysisResult:
    """
    Complete analysis result for an ingredient list.
    
    This is the primary output format for the analysis engine.
    """
    overall_verdict: str
    confidence_score: float
    risk_flags: List[RiskFlag]
    deception_alerts: List[DeceptionAlert]
    uncertainty_flags: List[Dict[str, Any]]
    safe_for_general_public: bool
    user_specific_warning: bool
    smart_swaps: List[SmartSwap]
    summary: str
    analyzed_profiles: List[str]
    timestamp: str
    ingredient_count: int
    error: bool = False
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def get_risk_count_by_severity(self) -> Dict[str, int]:
        """Count risks by severity level."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for flag in self.risk_flags:
            if flag.severity in counts:
                counts[flag.severity] += 1
        return counts
    
    def has_critical_risks(self) -> bool:
        """Check if any critical severity risks exist."""
        return any(flag.severity == "critical" for flag in self.risk_flags)


class IngredientParser:
    """
    Utility class for parsing and normalizing ingredient strings.
    """
    
    @staticmethod
    def parse(raw_ingredients: str) -> List[str]:
        """
        Parse a raw ingredient string into individual ingredients.
        
        Handles common formatting variations in ingredient lists.
        
        Args:
            raw_ingredients: Raw ingredient string from label
            
        Returns:
            List of individual ingredient strings
        """
        if not raw_ingredients:
            return []
        
        # Normalize the text
        text = raw_ingredients.strip()
        
        # Remove common prefixes
        prefixes_to_remove = [
            r"^ingredients?\s*:\s*",
            r"^contains?\s*:\s*",
        ]
        for pattern in prefixes_to_remove:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        # Split on common delimiters (comma, semicolon)
        # But preserve parenthetical content
        ingredients = []
        current = ""
        paren_depth = 0
        
        for char in text:
            if char == '(':
                paren_depth += 1
                current += char
            elif char == ')':
                paren_depth -= 1
                current += char
            elif char in ',;' and paren_depth == 0:
                if current.strip():
                    ingredients.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            ingredients.append(current.strip())
        
        return ingredients
    
    @staticmethod
    def normalize(ingredient: str) -> str:
        """
        Normalize an ingredient name for comparison.
        
        Args:
            ingredient: Raw ingredient string
            
        Returns:
            Normalized lowercase string
        """
        # Remove parenthetical content for comparison
        normalized = re.sub(r'\([^)]*\)', '', ingredient)
        # Normalize whitespace and case
        normalized = ' '.join(normalized.lower().split())
        return normalized


class RuleBasedChecker:
    """
    Rule-based pre-screening for common ingredient concerns.
    
    This provides fast, deterministic checks before LLM analysis.
    """
    
    # Known sugar aliases
    SUGAR_ALIASES = {
        "sucrose", "glucose", "fructose", "dextrose", "maltose", "lactose",
        "corn syrup", "high fructose corn syrup", "hfcs", "cane sugar",
        "cane juice", "evaporated cane juice", "brown rice syrup", "malt syrup",
        "barley malt", "maltodextrin", "dextrin", "treacle", "molasses",
        "agave", "agave nectar", "honey", "maple syrup", "coconut sugar",
        "date sugar", "turbinado", "muscovado", "demerara", "panela",
        "jaggery", "sucanat", "fruit juice concentrate", "grape juice concentrate"
    }
    
    # Known seed oils
    SEED_OILS = {
        "soybean oil", "canola oil", "rapeseed oil", "sunflower oil",
        "safflower oil", "corn oil", "cottonseed oil", "grapeseed oil",
        "rice bran oil", "vegetable oil"
    }
    
    # Known high-FODMAP ingredients
    HIGH_FODMAP = {
        "onion", "garlic", "wheat", "rye", "barley", "inulin", "chicory",
        "fructooligosaccharides", "fos", "galactooligosaccharides", "gos",
        "honey", "agave", "high fructose corn syrup", "apple", "pear",
        "mango", "watermelon", "sorbitol", "mannitol", "xylitol", "maltitol",
        "isomalt", "lactitol", "mushroom", "cauliflower", "artichoke"
    }
    
    # Known gluten sources
    GLUTEN_SOURCES = {
        "wheat", "barley", "rye", "malt", "brewer's yeast", "triticale",
        "spelt", "kamut", "semolina", "durum", "farina", "bulgur",
        "couscous", "seitan", "fu"
    }
    
    @classmethod
    def quick_screen(
        cls, 
        ingredients: List[str], 
        user_profile: UserProfile
    ) -> List[Dict[str, Any]]:
        """
        Perform quick rule-based screening of ingredients.
        
        This catches obvious issues before LLM analysis.
        
        Args:
            ingredients: List of parsed ingredients
            user_profile: User's health profile
            
        Returns:
            List of preliminary flags
        """
        flags = []
        
        for ingredient in ingredients:
            normalized = IngredientParser.normalize(ingredient)
            
            # Check for sugars (relevant to diabetes, PCOS, keto)
            sugar_profiles = {
                ProfileType.TYPE_2_DIABETES, 
                ProfileType.PCOS, 
                ProfileType.KETO
            }
            if sugar_profiles & set(user_profile.active_profiles):
                for sugar in cls.SUGAR_ALIASES:
                    if sugar in normalized:
                        flags.append({
                            "ingredient": ingredient,
                            "type": RiskType.HIDDEN_SUGAR,
                            "match": sugar,
                            "rule_based": True
                        })
                        break
            
            # Check for seed oils
            if ProfileType.AVOID_SEED_OILS in user_profile.active_profiles:
                for oil in cls.SEED_OILS:
                    if oil in normalized:
                        flags.append({
                            "ingredient": ingredient,
                            "type": RiskType.SEED_OIL,
                            "match": oil,
                            "rule_based": True
                        })
                        break
            
            # Check for high-FODMAP
            if ProfileType.IBS_LOW_FODMAP in user_profile.active_profiles:
                for fodmap in cls.HIGH_FODMAP:
                    if fodmap in normalized:
                        flags.append({
                            "ingredient": ingredient,
                            "type": RiskType.HIGH_FODMAP,
                            "match": fodmap,
                            "rule_based": True
                        })
                        break
            
            # Check for gluten
            if ProfileType.CELIAC in user_profile.active_profiles:
                for gluten in cls.GLUTEN_SOURCES:
                    if gluten in normalized:
                        flags.append({
                            "ingredient": ingredient,
                            "type": RiskType.CONTAINS_GLUTEN,
                            "match": gluten,
                            "rule_based": True
                        })
                        break
        
        return flags


def analyze_ingredients(
    ingredients: str,
    user_profile: UserProfile,
    client: Optional[GroqClient] = None,
    include_deception_check: bool = True
) -> AnalysisResult:
    """
    Main analysis function for ingredient lists.
    
    This is the primary entry point for the LabelLens analysis engine.
    It combines rule-based screening with LLM-powered semantic analysis.
    
    Args:
        ingredients: Raw ingredient string from food label
        user_profile: User's health profile configuration
        client: Optional GroqClient (uses singleton if not provided)
        include_deception_check: Whether to run additional deception detection
        
    Returns:
        AnalysisResult with complete analysis
    """
    # Parse ingredients
    parsed = IngredientParser.parse(ingredients)
    
    # Quick validation
    if not parsed:
        return AnalysisResult(
            overall_verdict=Verdict.CAUTION,
            confidence_score=0.0,
            risk_flags=[],
            deception_alerts=[],
            uncertainty_flags=[],
            safe_for_general_public=True,
            user_specific_warning=False,
            smart_swaps=[],
            summary="No ingredients could be parsed from the input.",
            analyzed_profiles=[],
            timestamp=datetime.utcnow().isoformat(),
            ingredient_count=0,
            error=True,
            error_message="No ingredients found"
        )
    
    if not user_profile.active_profiles and not user_profile.custom_restrictions:
        return AnalysisResult(
            overall_verdict=Verdict.CAUTION,
            confidence_score=0.0,
            risk_flags=[],
            deception_alerts=[],
            uncertainty_flags=[],
            safe_for_general_public=True,
            user_specific_warning=False,
            smart_swaps=[],
            summary="Please select at least one health profile to analyze ingredients.",
            analyzed_profiles=[],
            timestamp=datetime.utcnow().isoformat(),
            ingredient_count=len(parsed),
            error=True,
            error_message="No profiles selected"
        )
    
    # Perform rule-based quick screen
    rule_flags = RuleBasedChecker.quick_screen(parsed, user_profile)
    logger.debug(f"Rule-based screening found {len(rule_flags)} potential issues")
    
    # Get LLM client
    llm_client = client or get_client()
    
    # Perform LLM analysis
    llm_result = llm_client.analyze_ingredients(ingredients, user_profile)
    
    if llm_result.get("error"):
        return AnalysisResult(
            overall_verdict=Verdict.CAUTION,
            confidence_score=0.0,
            risk_flags=[],
            deception_alerts=[],
            uncertainty_flags=[],
            safe_for_general_public=True,
            user_specific_warning=False,
            smart_swaps=[],
            summary=llm_result.get("summary", "Analysis failed"),
            analyzed_profiles=user_profile.get_display_names(),
            timestamp=datetime.utcnow().isoformat(),
            ingredient_count=len(parsed),
            error=True,
            error_message=llm_result.get("error_message", "Unknown error")
        )
    
    # Convert LLM results to typed objects
    risk_flags = [
        RiskFlag(
            ingredient=rf.get("ingredient", "Unknown"),
            risk_type=rf.get("risk_type", "unknown"),
            severity=rf.get("severity", "medium"),
            explanation=rf.get("explanation", ""),
            relevant_profiles=rf.get("relevant_profiles", [])
        )
        for rf in llm_result.get("risk_flags", [])
    ]
    
    deception_alerts = [
        DeceptionAlert(
            claim=da.get("claim", ""),
            reality=da.get("reality", ""),
            concern_level=da.get("concern_level", "medium")
        )
        for da in llm_result.get("deception_alerts", [])
    ]
    
    smart_swaps = [
        SmartSwap(
            avoid=ss.get("avoid", ""),
            try_instead=ss.get("try_instead", ""),
            reason=ss.get("reason", "")
        )
        for ss in llm_result.get("smart_swaps", [])
    ]
    
    return AnalysisResult(
        overall_verdict=llm_result.get("overall_verdict", Verdict.CAUTION),
        confidence_score=llm_result.get("confidence_score", 0.5),
        risk_flags=risk_flags,
        deception_alerts=deception_alerts,
        uncertainty_flags=llm_result.get("uncertainty_flags", []),
        safe_for_general_public=llm_result.get("safe_for_general_public", True),
        user_specific_warning=llm_result.get("user_specific_warning", False),
        smart_swaps=smart_swaps,
        summary=llm_result.get("summary", "Analysis complete."),
        analyzed_profiles=user_profile.get_display_names(),
        timestamp=datetime.utcnow().isoformat(),
        ingredient_count=len(parsed),
        error=False
    )


def detect_semantic_deception(
    ingredients: str,
    product_claims: Optional[List[str]] = None,
    client: Optional[GroqClient] = None
) -> Dict[str, Any]:
    """
    Detect deceptive marketing or misleading labeling.
    
    This function specifically looks for ways that food labels
    can be technically accurate but misleading to consumers.
    
    Args:
        ingredients: Raw ingredient string
        product_claims: Optional marketing claims on the package
        client: Optional GroqClient
        
    Returns:
        Dictionary with deception analysis
    """
    llm_client = client or get_client()
    return llm_client.detect_semantic_deception(ingredients, product_claims)


def generate_risk_report(
    result: AnalysisResult,
    format: str = "markdown"
) -> str:
    """
    Generate a human-readable risk report from analysis results.
    
    Args:
        result: AnalysisResult from analyze_ingredients
        format: Output format ("markdown" or "plain")
        
    Returns:
        Formatted report string
    """
    if format == "markdown":
        return _generate_markdown_report(result)
    else:
        return _generate_plain_report(result)


def _generate_markdown_report(result: AnalysisResult) -> str:
    """Generate markdown-formatted report."""
    
    # Verdict emoji mapping
    verdict_emoji = {
        Verdict.SAFE: "✅",
        Verdict.CAUTION: "⚠️",
        Verdict.AVOID: "🚫"
    }
    
    emoji = verdict_emoji.get(result.overall_verdict, "❓")
    
    lines = [
        f"# LabelLens Analysis Report",
        f"",
        f"## Overall Verdict: {emoji} {result.overall_verdict}",
        f"",
        f"**Confidence:** {result.confidence_score:.0%}",
        f"",
        f"**Analyzed for:** {', '.join(result.analyzed_profiles)}",
        f"",
        f"### Summary",
        f"{result.summary}",
        f"",
    ]
    
    # Risk flags section
    if result.risk_flags:
        lines.append("## ⚠️ Risk Flags")
        lines.append("")
        for flag in result.risk_flags:
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }.get(flag.severity, "⚪")
            
            lines.append(f"### {severity_emoji} {flag.ingredient}")
            lines.append(f"- **Risk Type:** {flag.risk_type.replace('_', ' ').title()}")
            lines.append(f"- **Severity:** {flag.severity.title()}")
            lines.append(f"- **Explanation:** {flag.explanation}")
            if flag.relevant_profiles:
                lines.append(f"- **Affects:** {', '.join(flag.relevant_profiles)}")
            lines.append("")
    
    # Deception alerts
    if result.deception_alerts:
        lines.append("## 🎭 Deception Alerts")
        lines.append("")
        for alert in result.deception_alerts:
            lines.append(f"- **Claim:** {alert.claim}")
            lines.append(f"  - **Reality:** {alert.reality}")
            lines.append("")
    
    # Uncertainty flags
    if result.uncertainty_flags:
        lines.append("## ❓ Uncertainty Flags")
        lines.append("")
        for flag in result.uncertainty_flags:
            lines.append(f"- **{flag.get('ingredient', 'Unknown')}**")
            concerns = flag.get('possible_concerns', [])
            if concerns:
                lines.append(f"  - Possible concerns: {', '.join(concerns)}")
            rec = flag.get('recommendation', '')
            if rec:
                lines.append(f"  - Recommendation: {rec}")
            lines.append("")
    
    # Smart swaps
    if result.smart_swaps:
        lines.append("## 💡 Smart Swaps")
        lines.append("")
        for swap in result.smart_swaps:
            lines.append(f"- **Instead of:** {swap.avoid}")
            lines.append(f"  - **Try:** {swap.try_instead}")
            lines.append(f"  - **Why:** {swap.reason}")
            lines.append("")
    
    # Footer
    lines.extend([
        "---",
        f"*Analysis performed at {result.timestamp}*",
        "",
        "*Disclaimer: This analysis is for informational purposes only and does not constitute medical advice.*"
    ])
    
    return "\n".join(lines)


def _generate_plain_report(result: AnalysisResult) -> str:
    """Generate plain text report."""
    
    lines = [
        "LABELLENS ANALYSIS REPORT",
        "=" * 30,
        "",
        f"VERDICT: {result.overall_verdict}",
        f"Confidence: {result.confidence_score:.0%}",
        f"Profiles: {', '.join(result.analyzed_profiles)}",
        "",
        "SUMMARY:",
        result.summary,
        "",
    ]
    
    if result.risk_flags:
        lines.append("RISK FLAGS:")
        lines.append("-" * 20)
        for flag in result.risk_flags:
            lines.append(f"• {flag.ingredient} [{flag.severity}]")
            lines.append(f"  Type: {flag.risk_type}")
            lines.append(f"  {flag.explanation}")
            lines.append("")
    
    if result.smart_swaps:
        lines.append("SMART SWAPS:")
        lines.append("-" * 20)
        for swap in result.smart_swaps:
            lines.append(f"• Instead of {swap.avoid}, try {swap.try_instead}")
            lines.append(f"  ({swap.reason})")
            lines.append("")
    
    return "\n".join(lines)
