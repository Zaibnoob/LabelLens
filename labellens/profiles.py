"""
Health Profile System for LabelLens.

Defines user health profiles and their associated dietary restrictions,
concerns, and ingredient watchlists.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class ProfileType(Enum):
    """Available health profile types."""
    TYPE_2_DIABETES = "type_2_diabetes"
    PCOS = "pcos"
    HYPERTENSION = "hypertension"
    IBS_LOW_FODMAP = "ibs_low_fodmap"
    CELIAC = "celiac"
    NUT_ALLERGY = "nut_allergy"
    KIDNEY_DISEASE = "kidney_disease"
    KETO = "keto"
    AVOID_SEED_OILS = "avoid_seed_oils"
    # Common Indian health conditions
    THYROID_HYPOTHYROID = "thyroid_hypothyroid"
    HEART_DISEASE = "heart_disease"
    LACTOSE_INTOLERANCE = "lactose_intolerance"
    GOUT_HIGH_URIC_ACID = "gout_high_uric_acid"
    FATTY_LIVER = "fatty_liver"
    GASTRITIS_GERD = "gastritis_gerd"


@dataclass
class HealthProfile:
    """
    Represents a user's health profile with associated dietary considerations.
    
    Attributes:
        profile_type: The type of health condition/preference
        display_name: Human-readable name for UI
        description: Brief description of the profile
        primary_concerns: Main ingredients/compounds to watch for
        avoid_keywords: Keywords that typically indicate problematic ingredients
        clinical_context: Context for LLM to understand the medical background
    """
    profile_type: ProfileType
    display_name: str
    description: str
    primary_concerns: List[str]
    avoid_keywords: List[str]
    clinical_context: str
    severity_level: str = "moderate"  # low, moderate, high


# Pre-defined health profiles with clinical context
HEALTH_PROFILES: Dict[ProfileType, HealthProfile] = {
    ProfileType.TYPE_2_DIABETES: HealthProfile(
        profile_type=ProfileType.TYPE_2_DIABETES,
        display_name="Type 2 Diabetes",
        description="Blood sugar management focus",
        primary_concerns=[
            "hidden sugars", "high glycemic ingredients", "refined carbohydrates",
            "sugar alcohols (in excess)", "fruit juice concentrates"
        ],
        avoid_keywords=[
            "sugar", "syrup", "dextrose", "maltodextrin", "fructose", 
            "corn syrup", "honey", "agave", "molasses", "sucrose",
            "glucose", "cane juice", "rice syrup", "malt"
        ],
        clinical_context="""
        Patient has Type 2 Diabetes requiring careful blood glucose management.
        Hidden sugars and high-glycemic ingredients can cause dangerous blood sugar spikes.
        Even "natural" sugars like honey or agave are problematic.
        Watch for sugar alcohols which may still affect blood sugar.
        Maltodextrin has a higher glycemic index than table sugar.
        """
    ),
    
    ProfileType.PCOS: HealthProfile(
        profile_type=ProfileType.PCOS,
        display_name="PCOS (Polycystic Ovary Syndrome)",
        description="Insulin resistance and hormonal balance focus",
        primary_concerns=[
            "insulin-spiking ingredients", "inflammatory oils", 
            "excess dairy", "refined carbohydrates", "endocrine disruptors"
        ],
        avoid_keywords=[
            "sugar", "high fructose corn syrup", "refined flour", 
            "soybean oil", "vegetable oil", "dairy", "whey"
        ],
        clinical_context="""
        Patient has PCOS with associated insulin resistance and hormonal imbalance.
        Blood sugar spikes worsen insulin resistance and hormonal symptoms.
        Inflammatory seed oils may exacerbate inflammation.
        Some evidence suggests dairy can affect hormonal balance in PCOS.
        Focus on low-glycemic, anti-inflammatory ingredients.
        """
    ),
    
    ProfileType.HYPERTENSION: HealthProfile(
        profile_type=ProfileType.HYPERTENSION,
        display_name="Hypertension (High Blood Pressure)",
        description="Sodium and cardiovascular health focus",
        primary_concerns=[
            "high sodium content", "hidden salts", "MSG", 
            "processed ingredients", "saturated fats"
        ],
        avoid_keywords=[
            "sodium", "salt", "msg", "monosodium glutamate", 
            "sodium nitrate", "sodium phosphate", "soy sauce",
            "brine", "bouillon", "hydrolyzed"
        ],
        clinical_context="""
        Patient has hypertension requiring strict sodium limitation.
        Hidden sodium in processed foods is a major concern.
        MSG and sodium phosphates add significant sodium load.
        Even "low sodium" products may contain too much for strict diets.
        Watch for sodium in unexpected places like baked goods and cereals.
        """
    ),
    
    ProfileType.IBS_LOW_FODMAP: HealthProfile(
        profile_type=ProfileType.IBS_LOW_FODMAP,
        display_name="IBS (Low-FODMAP Diet)",
        description="Digestive health and FODMAP restriction focus",
        primary_concerns=[
            "high-FODMAP ingredients", "fermentable sugars", 
            "lactose", "fructose in excess of glucose", "sugar alcohols",
            "garlic", "onion", "wheat"
        ],
        avoid_keywords=[
            "onion", "garlic", "wheat", "lactose", "inulin", "chicory",
            "fructose", "honey", "agave", "apple", "pear", "mango",
            "sorbitol", "mannitol", "xylitol", "maltitol", "isomalt",
            "fructooligosaccharides", "galactooligosaccharides"
        ],
        clinical_context="""
        Patient follows low-FODMAP diet for IBS symptom management.
        FODMAPs (Fermentable Oligo-, Di-, Mono-saccharides And Polyols) trigger symptoms.
        Even small amounts of garlic or onion powder can cause flare-ups.
        Inulin and chicory root are HIGH FODMAP despite being marketed as fiber.
        "Natural flavors" often contain hidden garlic or onion.
        """
    ),
    
    ProfileType.CELIAC: HealthProfile(
        profile_type=ProfileType.CELIAC,
        display_name="Celiac Disease (Gluten-Free)",
        description="Strict gluten avoidance required",
        primary_concerns=[
            "gluten-containing grains", "cross-contamination risks",
            "hidden gluten in additives", "malt-based ingredients"
        ],
        avoid_keywords=[
            "wheat", "barley", "rye", "malt", "brewer's yeast",
            "triticale", "spelt", "kamut", "semolina", "durum",
            "farina", "bulgur", "couscous", "seitan", "fu"
        ],
        clinical_context="""
        Patient has Celiac Disease - even trace gluten causes intestinal damage.
        Cross-contamination is a serious concern with "may contain" warnings.
        Malt flavoring, malt vinegar, and brewer's yeast contain gluten.
        "Modified food starch" may be wheat-derived unless specified.
        Oats must be certified gluten-free due to contamination risk.
        """
    ),
    
    ProfileType.NUT_ALLERGY: HealthProfile(
        profile_type=ProfileType.NUT_ALLERGY,
        display_name="Nut Allergy",
        description="Tree nut and peanut avoidance (potentially life-threatening)",
        primary_concerns=[
            "tree nuts", "peanuts", "cross-contamination",
            "nut oils", "nut-derived ingredients"
        ],
        avoid_keywords=[
            "peanut", "almond", "cashew", "walnut", "pecan", "pistachio",
            "hazelnut", "macadamia", "brazil nut", "pine nut", "chestnut",
            "praline", "marzipan", "nougat", "nut oil", "arachis"
        ],
        clinical_context="""
        Patient has nut allergy - potential anaphylaxis risk.
        This is a SAFETY-CRITICAL profile with zero tolerance.
        Cross-contamination warnings ("may contain", "processed in facility") are serious.
        "Arachis oil" is peanut oil. Some refined nut oils may be tolerated but err on caution.
        Natural flavors and hydrolyzed proteins may contain nut derivatives.
        """,
        severity_level="high"
    ),
    
    ProfileType.KIDNEY_DISEASE: HealthProfile(
        profile_type=ProfileType.KIDNEY_DISEASE,
        display_name="Kidney Disease (Renal Diet)",
        description="Protein, potassium, phosphorus, and sodium management",
        primary_concerns=[
            "high protein content", "phosphate additives",
            "high potassium ingredients", "sodium"
        ],
        avoid_keywords=[
            "phosphate", "phosphoric acid", "potassium chloride",
            "protein isolate", "protein concentrate", "sodium"
        ],
        clinical_context="""
        Patient has kidney disease requiring careful management of:
        - Protein (excess burdens kidneys)
        - Phosphorus (phosphate additives are highly bioavailable and harmful)
        - Potassium (can accumulate to dangerous levels)
        - Sodium (fluid retention and blood pressure)
        Phosphate additives (sodium phosphate, calcium phosphate) are especially problematic.
        """
    ),
    
    ProfileType.KETO: HealthProfile(
        profile_type=ProfileType.KETO,
        display_name="Ketogenic Diet",
        description="Very low carbohydrate, high fat diet",
        primary_concerns=[
            "hidden carbohydrates", "sugars", "starches",
            "maltodextrin", "high-carb thickeners"
        ],
        avoid_keywords=[
            "sugar", "starch", "flour", "corn", "rice", "potato",
            "maltodextrin", "dextrin", "syrup", "honey", "molasses"
        ],
        clinical_context="""
        Patient follows ketogenic diet requiring <20-50g net carbs per day.
        Hidden carbs can kick them out of ketosis.
        Maltodextrin is essentially sugar despite low "sugar" labeling.
        Some sugar alcohols (maltitol) still significantly impact blood sugar.
        "Keto-friendly" marketing doesn't guarantee actual keto compatibility.
        """
    ),
    
    ProfileType.AVOID_SEED_OILS: HealthProfile(
        profile_type=ProfileType.AVOID_SEED_OILS,
        display_name="Avoid Seed Oils",
        description="Avoiding industrial seed/vegetable oils",
        primary_concerns=[
            "industrial seed oils", "vegetable oils",
            "high omega-6 oils", "refined oils"
        ],
        avoid_keywords=[
            "soybean oil", "canola oil", "sunflower oil", "safflower oil",
            "corn oil", "cottonseed oil", "grapeseed oil", "rice bran oil",
            "vegetable oil", "margarine", "shortening"
        ],
        clinical_context="""
        Patient avoids industrial seed oils due to concerns about:
        - High omega-6 to omega-3 ratio (potentially inflammatory)
        - Oxidation during processing and cooking
        - Potential metabolic effects
        Preferred alternatives: olive oil, coconut oil, butter, avocado oil, tallow.
        "Vegetable oil" is typically soybean or canola blend.
        """
    ),
    
    # Common Indian Health Conditions
    ProfileType.THYROID_HYPOTHYROID: HealthProfile(
        profile_type=ProfileType.THYROID_HYPOTHYROID,
        display_name="Thyroid (Hypothyroidism)",
        description="Thyroid function and metabolism support",
        primary_concerns=[
            "goitrogens", "soy products", "excessive iodine",
            "gluten (for Hashimoto's)", "processed foods", "refined sugars"
        ],
        avoid_keywords=[
            "soy", "soya", "soybean", "tofu", "edamame", "soy protein",
            "soy lecithin", "cabbage", "broccoli", "cauliflower", "kale",
            "millet", "pearl millet", "bajra", "ragi"
        ],
        clinical_context="""
        Patient has hypothyroidism requiring careful dietary management.
        Goitrogens (found in raw cruciferous vegetables, soy, millets) can interfere with thyroid function.
        Soy products may interfere with thyroid hormone absorption.
        For Hashimoto's thyroiditis, gluten may trigger autoimmune response.
        Processed foods and refined sugars can slow metabolism further.
        Cooking reduces goitrogenic activity in vegetables.
        Millets like bajra and ragi are commonly consumed in India but contain goitrogens.
        """
    ),
    
    ProfileType.HEART_DISEASE: HealthProfile(
        profile_type=ProfileType.HEART_DISEASE,
        display_name="Heart Disease (Cardiovascular)",
        description="Heart health and cholesterol management",
        primary_concerns=[
            "trans fats", "saturated fats", "high sodium",
            "cholesterol", "refined sugars", "processed meats"
        ],
        avoid_keywords=[
            "hydrogenated", "partially hydrogenated", "trans fat", "vanaspati",
            "dalda", "margarine", "shortening", "palm oil", "coconut oil",
            "ghee", "butter", "cream", "lard", "sodium", "salt",
            "bacon", "sausage", "salami", "processed meat"
        ],
        clinical_context="""
        Patient has cardiovascular disease or high cholesterol.
        Trans fats (vanaspati/dalda common in Indian cooking) are extremely harmful.
        Saturated fats should be limited for heart health.
        High sodium increases blood pressure and cardiac strain.
        Processed meats contain sodium, nitrates, and saturated fats.
        In Indian context, watch for: vanaspati, excessive ghee, fried snacks (namkeen).
        Refined sugars contribute to inflammation and metabolic issues.
        """
    ),
    
    ProfileType.LACTOSE_INTOLERANCE: HealthProfile(
        profile_type=ProfileType.LACTOSE_INTOLERANCE,
        display_name="Lactose Intolerance",
        description="Dairy and lactose avoidance",
        primary_concerns=[
            "milk products", "hidden dairy", "lactose",
            "whey", "casein", "milk solids"
        ],
        avoid_keywords=[
            "milk", "lactose", "whey", "casein", "curd", "dahi", "paneer",
            "cheese", "cream", "butter", "ghee", "khoya", "mawa",
            "milk powder", "skim milk", "buttermilk", "lassi", "chaas",
            "yogurt", "ice cream", "kulfi", "rabri", "condensed milk"
        ],
        clinical_context="""
        Patient has lactose intolerance - cannot digest lactose in dairy.
        Very common in India (60-70% of adult population).
        Indian dairy products to watch: paneer, dahi/curd, khoya/mawa, lassi, chaas.
        Ghee and butter have minimal lactose and may be tolerated.
        Whey and casein in protein supplements and processed foods cause issues.
        "Milk solids" and "non-fat milk solids" contain lactose.
        Many Indian sweets (mithai) contain khoya, condensed milk, or milk powder.
        """
    ),
    
    ProfileType.GOUT_HIGH_URIC_ACID: HealthProfile(
        profile_type=ProfileType.GOUT_HIGH_URIC_ACID,
        display_name="Gout / High Uric Acid",
        description="Purine restriction for uric acid management",
        primary_concerns=[
            "high-purine foods", "organ meats", "seafood",
            "alcohol", "fructose", "yeast"
        ],
        avoid_keywords=[
            "liver", "kidney", "brain", "organ meat", "offal",
            "sardine", "anchovy", "mackerel", "herring", "shellfish",
            "prawn", "shrimp", "crab", "lobster", "mussel",
            "yeast", "brewer's yeast", "beer", "wine", "alcohol",
            "high fructose corn syrup", "fructose"
        ],
        clinical_context="""
        Patient has gout or hyperuricemia (high uric acid levels).
        High-purine foods break down to uric acid, causing painful flare-ups.
        Organ meats (common in Indian cuisine: liver, kidney, brain) are highest in purines.
        Seafood, especially shellfish and certain fish, are high in purines.
        Alcohol (especially beer) significantly raises uric acid levels.
        Fructose increases uric acid production.
        Moderate protein from plant sources and low-fat dairy are safer.
        Stay hydrated to help flush uric acid.
        """
    ),
    
    ProfileType.FATTY_LIVER: HealthProfile(
        profile_type=ProfileType.FATTY_LIVER,
        display_name="Fatty Liver (NAFLD)",
        description="Liver health and fat reduction focus",
        primary_concerns=[
            "added sugars", "fructose", "refined carbohydrates",
            "saturated fats", "alcohol", "processed foods"
        ],
        avoid_keywords=[
            "sugar", "fructose", "high fructose corn syrup", "corn syrup",
            "glucose syrup", "refined flour", "maida", "white bread",
            "alcohol", "beer", "wine", "spirits",
            "fried", "trans fat", "hydrogenated", "vanaspati"
        ],
        clinical_context="""
        Patient has Non-Alcoholic Fatty Liver Disease (NAFLD).
        Very common in urban India due to sedentary lifestyle and diet changes.
        Fructose is directly metabolized by liver and promotes fat accumulation.
        Refined carbohydrates (maida/refined flour) spike insulin and promote liver fat.
        Alcohol must be completely avoided as it directly damages liver.
        Fried foods and trans fats worsen liver inflammation.
        In Indian context: avoid sweets, mithai, packaged snacks, maida-based foods.
        Focus on whole grains, vegetables, and lean proteins.
        """
    ),
    
    ProfileType.GASTRITIS_GERD: HealthProfile(
        profile_type=ProfileType.GASTRITIS_GERD,
        display_name="Gastritis / Acid Reflux (GERD)",
        description="Stomach acid and digestive comfort management",
        primary_concerns=[
            "acidic foods", "spicy foods", "caffeine",
            "fatty foods", "citrus", "trigger foods"
        ],
        avoid_keywords=[
            "chili", "chilli", "pepper", "spice", "masala", "hot sauce",
            "tomato", "citrus", "lemon", "orange", "lime", "vinegar",
            "coffee", "caffeine", "chocolate", "cocoa", "mint", "peppermint",
            "garlic", "onion", "fried", "carbonated", "soda", "alcohol"
        ],
        clinical_context="""
        Patient has gastritis or GERD (acid reflux).
        Extremely common in India due to spicy food culture.
        Spicy foods (chili, masala) directly irritate stomach lining.
        Acidic foods (tomatoes, citrus, vinegar) worsen acid reflux.
        Caffeine relaxes lower esophageal sphincter, allowing acid reflux.
        Fatty and fried foods delay stomach emptying, increasing reflux.
        Onion and garlic are common triggers (problematic in Indian cooking).
        Mint/peppermint relaxes LES and worsens reflux despite feeling soothing.
        Carbonated drinks increase stomach pressure.
        Eating smaller meals and avoiding late-night eating helps.
        """
    ),
}


@dataclass
class UserProfile:
    """
    Represents a user's complete health profile with multiple conditions.
    """
    active_profiles: List[ProfileType] = field(default_factory=list)
    custom_restrictions: List[str] = field(default_factory=list)
    severity_preference: str = "balanced"  # strict, balanced, lenient
    
    def get_combined_context(self) -> str:
        """Generate combined clinical context for all active profiles."""
        contexts = []
        for profile_type in self.active_profiles:
            if profile_type in HEALTH_PROFILES:
                profile = HEALTH_PROFILES[profile_type]
                contexts.append(f"**{profile.display_name}:**\n{profile.clinical_context}")
        
        if self.custom_restrictions:
            contexts.append(f"**Additional Restrictions:**\n{', '.join(self.custom_restrictions)}")
        
        return "\n\n".join(contexts)
    
    def get_all_avoid_keywords(self) -> List[str]:
        """Get combined list of all keywords to watch for."""
        keywords = set()
        for profile_type in self.active_profiles:
            if profile_type in HEALTH_PROFILES:
                keywords.update(HEALTH_PROFILES[profile_type].avoid_keywords)
        return list(keywords)
    
    def get_display_names(self) -> List[str]:
        """Get human-readable names for all active profiles."""
        names = []
        for profile_type in self.active_profiles:
            if profile_type in HEALTH_PROFILES:
                names.append(HEALTH_PROFILES[profile_type].display_name)
        # Include custom restriction names if they look like profile names
        for restriction in self.custom_restrictions:
            if ":" in restriction:
                # Extract the profile name from format "Name: Avoid [...]"
                profile_name = restriction.split(":")[0].strip()
                names.append(f"Custom: {profile_name}")
            else:
                names.append("Custom Profile")
        return names
    
    def has_high_severity_profile(self) -> bool:
        """Check if any profile is marked as high severity (e.g., allergies)."""
        for profile_type in self.active_profiles:
            if profile_type in HEALTH_PROFILES:
                if HEALTH_PROFILES[profile_type].severity_level == "high":
                    return True
        return False


def get_available_profiles() -> Dict[str, ProfileType]:
    """
    Returns a mapping of display names to profile types for UI selection.
    """
    return {
        HEALTH_PROFILES[pt].display_name: pt 
        for pt in HEALTH_PROFILES
    }
