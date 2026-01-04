# LabelLens: The Context-Aware Nutritional Auditor

🔍 **Your Personal Food Firewall**

LabelLens is an AI-powered food label analysis system that evaluates ingredient lists based on individual health profiles, not generic nutrition rules.

> *"This food may be healthy for others, but is it compatible with MY physiology?"*

## 🚀 Quick Start

### 1. Clone and Install

```bash
cd Encode26
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the project root:

```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

### 3. Run the App

```bash
streamlit run app.py
```

## 🎯 Features

### Health Profile System
Select from multiple health conditions:
- 🩺 Type 2 Diabetes
- 🩺 PCOS (Polycystic Ovary Syndrome)
- 🩺 Hypertension
- 🩺 IBS (Low-FODMAP Diet)
- 🩺 Celiac Disease (Gluten-Free)
- 🩺 Nut Allergy
- 🩺 Kidney Disease
- 🥑 Ketogenic Diet
- 🌻 Avoid Seed Oils

### Intelligent Analysis
- **Risk Flags**: Identifies ingredients problematic for YOUR profiles
- **Deception Detection**: Catches misleading marketing claims
- **Uncertainty Handling**: Flags ambiguous ingredients like "natural flavors"
- **Smart Swaps**: Suggests safer alternatives

### Output Format
```json
{
  "overall_verdict": "SAFE | CAUTION | AVOID",
  "risk_flags": [...],
  "deception_alerts": [...],
  "smart_swaps": [...],
  "summary": "Human-readable explanation"
}
```

## 📁 Project Structure

```
Encode26/
├── app.py                    # Streamlit frontend
├── requirements.txt          # Python dependencies
├── .env                      # API keys (create this)
├── .env.example              # Environment template
├── README.md                 # This file
└── labellens/
    ├── __init__.py           # Package init
    ├── config.py             # Configuration settings
    ├── profiles.py           # Health profile definitions
    ├── llm.py                # Gemini integration layer
    └── analyzer.py           # Core analysis engine
```

## 🔧 Core Functions

### `analyze_ingredients(ingredients, user_profile)`
Main analysis function that evaluates ingredients against user's health profiles.

```python
from labellens.profiles import UserProfile, ProfileType
from labellens.analyzer import analyze_ingredients

profile = UserProfile(active_profiles=[
    ProfileType.TYPE_2_DIABETES,
    ProfileType.AVOID_SEED_OILS
])

result = analyze_ingredients(
    ingredients="Sugar, Wheat Flour, Soybean Oil, Salt",
    user_profile=profile
)
```

### `detect_semantic_deception(ingredients, product_claims)`
Detects misleading labeling or marketing claims.

```python
from labellens.analyzer import detect_semantic_deception

result = detect_semantic_deception(
    ingredients="Maltodextrin, Rice Syrup, Fruit Juice Concentrate",
    product_claims=["No Added Sugar", "All Natural"]
)
```

### `generate_risk_report(result, format)`
Generates a human-readable report from analysis results.

```python
from labellens.analyzer import generate_risk_report

report = generate_risk_report(result, format="markdown")
```

## 🧠 How It Works

1. **Profile Injection**: User health profiles are injected into Gemini's system prompt
2. **Clinical Context**: Each profile includes medical context for accurate analysis
3. **Rule-Based Pre-Screen**: Fast deterministic checks for known problematic ingredients
4. **LLM Semantic Analysis**: Gemini reasons about ingredient safety and marketing claims
5. **Structured Output**: Results are returned in consistent JSON format

## ⚠️ Disclaimer

LabelLens provides **informational analysis only** and does not constitute medical advice. Always consult with healthcare professionals for dietary decisions related to medical conditions.

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **LLM**: Google Gemini 1.5 Flash
- **Validation**: Pydantic
- **Retry Logic**: Tenacity

## 📝 License

MIT License - See LICENSE file for details.

---

Built with ❤️ for health-conscious consumers everywhere.
