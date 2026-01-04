"""
LabelLens: The Context-Aware Nutritional Auditor

Mobile-First Streamlit Application with Camera Scanning

A personalized food label analysis system that evaluates ingredient lists
based on individual health profiles, not generic nutrition rules.
"""

import streamlit as st
from typing import List, Optional, Dict, Any
import json
import base64
from io import BytesIO
from datetime import datetime
import hashlib

# Import LabelLens modules
from labellens.profiles import (
    ProfileType, 
    UserProfile, 
    HEALTH_PROFILES,
    get_available_profiles
)
from labellens.analyzer import (
    analyze_ingredients,
    detect_semantic_deception,
    generate_risk_report,
    AnalysisResult
)
from labellens.config import Verdict, GROQ_API_KEY
from labellens.llm import extract_ingredients_from_image

# Page configuration - Mobile optimized
st.set_page_config(
    page_title="LabelLens",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"  # Better for mobile
)

# Modern Mobile-First CSS - Aesthetic Minimalist Design
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    /* CSS Variables for Eye-Catching Color Palette */
    :root {
        --bg-primary: #030014;
        --bg-secondary: #0a0a1f;
        --bg-card: rgba(255, 255, 255, 0.02);
        --bg-card-hover: rgba(255, 255, 255, 0.05);
        --accent-primary: #8b5cf6;
        --accent-secondary: #06b6d4;
        --accent-tertiary: #f472b6;
        --accent-glow: rgba(139, 92, 246, 0.5);
        --text-primary: #ffffff;
        --text-secondary: rgba(255, 255, 255, 0.75);
        --text-muted: rgba(255, 255, 255, 0.45);
        --success: #22c55e;
        --success-soft: rgba(34, 197, 94, 0.15);
        --warning: #eab308;
        --warning-soft: rgba(234, 179, 8, 0.15);
        --danger: #ef4444;
        --danger-soft: rgba(239, 68, 68, 0.15);
        --border-subtle: rgba(255, 255, 255, 0.06);
        --border-glow: rgba(139, 92, 246, 0.4);
        --gradient-primary: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 50%, #f472b6 100%);
        --gradient-text: linear-gradient(135deg, #fff 0%, #8b5cf6 50%, #06b6d4 100%);
    }
    
    /* Global Styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: var(--bg-primary);
        background-image: 
            radial-gradient(ellipse 100% 80% at 50% -30%, rgba(139, 92, 246, 0.2), transparent),
            radial-gradient(ellipse 80% 60% at 100% 100%, rgba(6, 182, 212, 0.15), transparent),
            radial-gradient(ellipse 60% 50% at 0% 80%, rgba(244, 114, 182, 0.12), transparent),
            radial-gradient(circle at 20% 50%, rgba(139, 92, 246, 0.08), transparent 40%);
        min-height: 100vh;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Main container */
    .main .block-container {
        padding: 1.5rem 1rem;
        max-width: 850px;
        margin: 0 auto;
    }
    
    /* Premium Glass Card styles */
    .glass-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(139, 92, 246, 0.03), rgba(255,255,255,0.01));
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        border-radius: 28px;
        padding: 2rem;
        margin: 1.25rem 0;
        border: 1px solid rgba(139, 92, 246, 0.15);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.5), rgba(6, 182, 212, 0.5), transparent);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .glass-card:hover {
        background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(139, 92, 246, 0.05), rgba(6, 182, 212, 0.02));
        border-color: rgba(6, 182, 212, 0.4);
        box-shadow: 0 15px 60px rgba(139, 92, 246, 0.15), 0 0 80px rgba(6, 182, 212, 0.08);
        transform: translateY(-4px);
    }
    
    .glass-card:hover::before {
        opacity: 1;
    }
    
    /* Header - Premium */
    .app-header {
        text-align: center;
        padding: 2.5rem 0 3rem 0;
        animation: fadeInDown 0.6s ease-out;
        position: relative;
    }
    
    .app-header::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 200px;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--accent-primary), var(--accent-secondary), transparent);
        opacity: 0.5;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes scaleIn {
        from {
            opacity: 0;
            transform: scale(0.9);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes bounceIn {
        0% {
            opacity: 0;
            transform: scale(0.3);
        }
        50% {
            transform: scale(1.05);
        }
        70% {
            transform: scale(0.9);
        }
        100% {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.08); opacity: 0.9; }
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 15px rgba(139, 92, 246, 0.4); }
        50% { box-shadow: 0 0 50px rgba(139, 92, 246, 0.7), 0 0 100px rgba(6, 182, 212, 0.4); }
    }
    
    @keyframes borderGlow {
        0%, 100% { border-color: rgba(139, 92, 246, 0.3); }
        50% { border-color: rgba(6, 182, 212, 0.8); }
    }
    
    @keyframes textGradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    @keyframes ripple {
        0% {
            transform: scale(0);
            opacity: 1;
        }
        100% {
            transform: scale(4);
            opacity: 0;
        }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0) rotate(0deg); }
        25% { transform: translateY(-10px) rotate(2deg); }
        75% { transform: translateY(10px) rotate(-2deg); }
    }
    
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    
    @keyframes aurora {
        0%, 100% { 
            opacity: 0.5;
            transform: translateX(0) scale(1);
        }
        33% { 
            opacity: 0.8;
            transform: translateX(50px) scale(1.2);
        }
        66% { 
            opacity: 0.6;
            transform: translateX(-50px) scale(0.9);
        }
    }
    
    /* Animated gradient text - Enhanced */
    .animated-gradient-text {
        background: linear-gradient(90deg, #8b5cf6, #06b6d4, #f472b6, #8b5cf6);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: textGradient 3s ease infinite;
    }
    
    .app-header h1 {
        font-size: 3.5rem;
        font-weight: 900;
        margin: 0;
        background: linear-gradient(90deg, #ffffff 0%, #8b5cf6 25%, #06b6d4 50%, #f472b6 75%, #ffffff 100%);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.03em;
        animation: textGradient 5s ease infinite;
        text-shadow: 0 0 60px rgba(139, 92, 246, 0.3);
    }
    
    .app-header .subtitle {
        font-size: 1.2rem;
        color: var(--text-secondary);
        margin-top: 1rem;
        font-weight: 400;
        letter-spacing: 0.02em;
        opacity: 0.9;
    }
    
    .app-header .tagline {
        display: inline-block;
        margin-top: 1.5rem;
        padding: 0.75rem 1.75rem;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(6, 182, 212, 0.15), rgba(244, 114, 182, 0.1));
        border: 1px solid rgba(139, 92, 246, 0.4);
        border-radius: 50px;
        font-size: 0.95rem;
        color: var(--accent-primary);
        font-weight: 600;
        animation: borderGlow 3s ease-in-out infinite, float 4s ease-in-out infinite;
        transition: all 0.3s ease;
        cursor: default;
    }
    
    .app-header .tagline:hover {
        transform: scale(1.05);
        box-shadow: 0 10px 40px rgba(139, 92, 246, 0.3);
    }
    
    /* Section headers - Premium */
    .section-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 1.5rem;
        letter-spacing: -0.02em;
        position: relative;
    }
    
    .section-header::before {
        content: '';
        width: 5px;
        height: 24px;
        background: linear-gradient(180deg, var(--accent-primary), var(--accent-secondary), var(--accent-tertiary));
        border-radius: 3px;
        box-shadow: 0 0 15px rgba(139, 92, 246, 0.5);
    }
    
    /* Verdict cards - Premium Glassmorphism */
    .verdict-safe {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(16, 185, 129, 0.08), rgba(52, 211, 153, 0.05));
        backdrop-filter: blur(20px);
        border: 2px solid rgba(34, 197, 94, 0.4);
        padding: 3rem;
        border-radius: 28px;
        text-align: center;
        position: relative;
        overflow: hidden;
        animation: scaleIn 0.5s ease-out;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .verdict-safe::before {
        content: '';
        position: absolute;
        top: -50%;
        left: 50%;
        transform: translateX(-50%);
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(34, 197, 94, 0.4), transparent 60%);
        pointer-events: none;
        animation: pulse 3s ease-in-out infinite;
    }
    
    .verdict-safe::after {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, transparent 40%, rgba(34, 197, 94, 0.1) 100%);
        pointer-events: none;
    }
    
    .verdict-safe:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 25px 60px rgba(34, 197, 94, 0.25), 0 0 100px rgba(34, 197, 94, 0.15);
        border-color: rgba(34, 197, 94, 0.6);
    }
    
    .verdict-caution {
        background: linear-gradient(135deg, rgba(234, 179, 8, 0.15), rgba(245, 158, 11, 0.08), rgba(251, 191, 36, 0.05));
        backdrop-filter: blur(20px);
        border: 2px solid rgba(234, 179, 8, 0.4);
        padding: 3rem;
        border-radius: 28px;
        text-align: center;
        position: relative;
        overflow: hidden;
        animation: scaleIn 0.5s ease-out;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .verdict-caution::before {
        content: '';
        position: absolute;
        top: -50%;
        left: 50%;
        transform: translateX(-50%);
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(234, 179, 8, 0.4), transparent 60%);
        pointer-events: none;
        animation: pulse 3s ease-in-out infinite;
    }
    
    .verdict-caution::after {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, transparent 40%, rgba(234, 179, 8, 0.1) 100%);
        pointer-events: none;
    }
    
    .verdict-caution:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 25px 60px rgba(234, 179, 8, 0.25), 0 0 100px rgba(234, 179, 8, 0.15);
        border-color: rgba(234, 179, 8, 0.6);
    }
    
    .verdict-avoid {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(248, 113, 113, 0.08), rgba(252, 165, 165, 0.05));
        backdrop-filter: blur(20px);
        border: 2px solid rgba(239, 68, 68, 0.4);
        padding: 3rem;
        border-radius: 28px;
        text-align: center;
        position: relative;
        overflow: hidden;
        animation: scaleIn 0.5s ease-out, shake 0.5s ease-out 0.5s;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .verdict-avoid::before {
        content: '';
        position: absolute;
        top: -50%;
        left: 50%;
        transform: translateX(-50%);
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(239, 68, 68, 0.4), transparent 60%);
        pointer-events: none;
        animation: pulse 2s ease-in-out infinite;
    }
    
    .verdict-avoid::after {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, transparent 40%, rgba(239, 68, 68, 0.1) 100%);
        pointer-events: none;
    }
    
    .verdict-avoid:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 25px 60px rgba(239, 68, 68, 0.25), 0 0 100px rgba(239, 68, 68, 0.15);
        border-color: rgba(239, 68, 68, 0.6);
    }
    
    .verdict-icon {
        font-size: 5rem;
        margin-bottom: 1rem;
        position: relative;
        z-index: 1;
        animation: bounceIn 0.6s ease-out;
        filter: drop-shadow(0 0 20px currentColor);
    }
    
    .verdict-text {
        font-size: 2.25rem;
        font-weight: 800;
        margin: 0;
        color: var(--text-primary);
        letter-spacing: -0.03em;
        position: relative;
        z-index: 1;
    }
    
    .verdict-subtitle {
        font-size: 1.1rem;
        color: var(--text-secondary);
        margin-top: 0.75rem;
        position: relative;
        z-index: 1;
    }
    
    /* Risk flag cards - Premium Glass */
    .risk-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        backdrop-filter: blur(10px);
        border-radius: 18px;
        padding: 1.5rem;
        margin: 0.75rem 0;
        border-left: 4px solid;
        border-top: 1px solid var(--border-subtle);
        border-right: 1px solid var(--border-subtle);
        border-bottom: 1px solid var(--border-subtle);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .risk-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.03), transparent);
        transform: translateX(-100%);
        transition: transform 0.6s ease;
    }
    
    .risk-card:hover::before {
        transform: translateX(100%);
    }
    
    .risk-card:hover {
        background: var(--bg-card-hover);
        transform: translateX(6px) scale(1.01);
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    }
    
    .risk-critical { 
        border-left-color: var(--danger); 
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.05));
    }
    .risk-high { 
        border-left-color: #f97316; 
        background: linear-gradient(135deg, rgba(249, 115, 22, 0.15), rgba(249, 115, 22, 0.05));
    }
    .risk-medium { 
        border-left-color: var(--warning); 
        background: linear-gradient(135deg, rgba(234, 179, 8, 0.15), rgba(234, 179, 8, 0.05));
    }
    .risk-low { 
        border-left-color: var(--success); 
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(34, 197, 94, 0.05));
    }
    
    .risk-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-weight: 600;
        font-size: 1.05rem;
        color: var(--text-primary);
    }
    
    .risk-badge {
        padding: 0.3rem 0.85rem;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-secondary);
    }
    
    .risk-body {
        margin-top: 0.75rem;
        font-size: 0.92rem;
        color: var(--text-secondary);
        line-height: 1.7;
    }
    
    /* Smart swap cards - Premium Gradient */
    .swap-card {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.12), rgba(6, 182, 212, 0.08), rgba(244, 114, 182, 0.08));
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 22px;
        padding: 1.75rem;
        margin: 0.75rem 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .swap-card::after {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, transparent 40%, rgba(139, 92, 246, 0.1));
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .swap-card:hover {
        border-color: rgba(6, 182, 212, 0.5);
        box-shadow: 0 0 40px rgba(139, 92, 246, 0.2), 0 0 60px rgba(6, 182, 212, 0.1);
        transform: translateY(-3px);
    }
    
    .swap-card:hover::after {
        opacity: 1;
    }
    
    .swap-arrow {
        text-align: center;
        font-size: 1.75rem;
        color: var(--accent-secondary);
        animation: float 2s ease-in-out infinite;
    }
    
    /* Input styling - Premium Glass */
    .stTextArea textarea {
        background: linear-gradient(135deg, rgba(15, 15, 30, 0.9), rgba(10, 10, 31, 0.8)) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 18px !important;
        padding: 1.5rem !important;
        font-size: 1rem !important;
        color: var(--text-primary) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        backdrop-filter: blur(10px);
    }
    
    .stTextArea textarea:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 4px var(--accent-glow), 0 0 40px rgba(139, 92, 246, 0.2) !important;
    }
    
    .stTextArea textarea::placeholder {
        color: var(--text-muted) !important;
    }
    
    /* Button styling - Premium Glowing with Shimmer */
    .stButton > button {
        border-radius: 16px !important;
        padding: 1rem 2.25rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        letter-spacing: 0.03em !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        border: none !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s ease;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 50%, var(--accent-tertiary) 100%) !important;
        background-size: 200% 200% !important;
        color: white !important;
        box-shadow: 0 4px 25px var(--accent-glow), 0 0 60px rgba(6, 182, 212, 0.2) !important;
        animation: glow 4s ease-in-out infinite, textGradient 4s ease infinite;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-4px) scale(1.03) !important;
        box-shadow: 0 15px 50px var(--accent-glow), 0 0 80px rgba(6, 182, 212, 0.3) !important;
    }
    
    .stButton > button[kind="primary"]:active {
        transform: translateY(-1px) scale(0.98) !important;
    }
    
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01)) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-subtle) !important;
        backdrop-filter: blur(10px);
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(6, 182, 212, 0.05)) !important;
        border-color: var(--accent-primary) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 10px 35px rgba(0, 0, 0, 0.3), 0 0 30px rgba(139, 92, 246, 0.15) !important;
    }
    
    /* Camera input - Premium Glass */
    .stCameraInput > div {
        border-radius: 24px !important;
        overflow: hidden;
        border: 2px dashed rgba(139, 92, 246, 0.3) !important;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), rgba(6, 182, 212, 0.02));
        transition: all 0.3s ease;
    }
    
    .stCameraInput > div:hover {
        border-color: var(--accent-secondary) !important;
        box-shadow: 0 0 30px rgba(6, 182, 212, 0.15);
    }
    
    /* Tabs - Premium Pills */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.75rem;
        background: transparent;
        border-bottom: 1px solid rgba(139, 92, 246, 0.2);
        padding-bottom: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        padding: 0.75rem 1.5rem;
        background: transparent;
        color: var(--text-muted);
        font-weight: 500;
        border: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    
    .stTabs [data-baseweb="tab"]::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 50%;
        width: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
        transition: all 0.3s ease;
        transform: translateX(-50%);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-primary);
        background: rgba(168, 85, 247, 0.1);
    }
    
    .stTabs [data-baseweb="tab"]:hover::after {
        width: 50%;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-bottom: none !important;
    }
    
    .stTabs [aria-selected="true"]::after {
        width: 80% !important;
    }
    
    /* Checkbox styling - Interactive toggle effect */
    .stCheckbox > label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        padding: 0.5rem 0.75rem !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    
    .stCheckbox > label:hover {
        background: rgba(168, 85, 247, 0.1) !important;
    }
    
    .stCheckbox > label > span[data-testid="stCheckbox"] {
        background: var(--bg-secondary) !important;
        border-color: var(--border-subtle) !important;
        transition: all 0.2s ease !important;
    }
    
    .stCheckbox > label:hover > span[data-testid="stCheckbox"] {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 10px rgba(168, 85, 247, 0.3) !important;
    }
    
    /* Checked state animation */
    .stCheckbox input:checked + span {
        animation: bounceIn 0.4s ease !important;
    }
    
    /* Info/Success/Error boxes with animation */
    .stAlert {
        border-radius: 14px !important;
        border: none !important;
        animation: slideInLeft 0.4s ease-out !important;
    }
    
    div[data-testid="stAlert"] > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 14px !important;
        color: var(--text-primary) !important;
    }
    
    /* Success alert special styling */
    div[data-testid="stAlert"][data-baseweb="notification"] {
        animation: bounceIn 0.5s ease-out !important;
    }
    
    /* File uploader - Interactive drop zone */
    section[data-testid="stFileUploadDropzone"] {
        background: var(--bg-secondary) !important;
        border: 2px dashed var(--border-subtle) !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        transition: all 0.3s ease !important;
    }
    
    section[data-testid="stFileUploadDropzone"]:hover {
        border-color: var(--accent-primary) !important;
        background: rgba(168, 85, 247, 0.05) !important;
        box-shadow: 0 0 20px rgba(168, 85, 247, 0.15) !important;
        transform: scale(1.01);
    }
    
    section[data-testid="stFileUploadDropzone"]:active {
        transform: scale(0.99);
    }
    
    section[data-testid="stFileUploadDropzone"] div div::before {
        content: "📷 Drop image or click to upload" !important;
        color: var(--text-secondary) !important;
    }
    section[data-testid="stFileUploadDropzone"] div div span { display: none; }
    section[data-testid="stFileUploadDropzone"] div div small { display: none; }
    
    /* Spinner with glow */
    .stSpinner > div {
        border-top-color: var(--accent-primary) !important;
        animation: spin 1s linear infinite, glow 2s ease-in-out infinite !important;
    }
    
    /* Confidence meter with animated fill */
    .confidence-meter {
        height: 6px;
        background: var(--bg-secondary);
        border-radius: 3px;
        overflow: hidden;
        margin-top: 0.75rem;
    }
    
    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary), var(--accent-tertiary));
        background-size: 200% 100%;
        border-radius: 3px;
        transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        animation: gradientShift 3s ease infinite;
    }
    
    @keyframes gradientShift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    /* Profile cards with staggered animation */
    .profile-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 0.75rem;
    }
    
    /* Download button with interactive effects */
    .stDownloadButton > button {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-primary) !important;
        border-radius: 14px !important;
        transition: all 0.3s ease !important;
        position: relative;
        overflow: hidden;
    }
    
    .stDownloadButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        background: rgba(168, 85, 247, 0.2);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        transition: width 0.4s ease, height 0.4s ease;
    }
    
    .stDownloadButton > button:hover {
        border-color: var(--accent-primary) !important;
        background: var(--bg-card-hover) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(168, 85, 247, 0.2) !important;
    }
    
    .stDownloadButton > button:hover::before {
        width: 300%;
        height: 300%;
    }
    
    .stDownloadButton > button:active {
        transform: translateY(0);
    }
    
    /* Number input with glow on focus */
    .stNumberInput input {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-primary) !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    
    .stNumberInput input:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 15px rgba(168, 85, 247, 0.3) !important;
        outline: none !important;
    }
    
    /* Selectbox with smooth transitions */
    .stSelectbox > div > div {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    
    .stSelectbox > div > div:hover {
        border-color: var(--accent-primary) !important;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 15px rgba(168, 85, 247, 0.2) !important;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem 0.75rem;
        }
        
        .app-header h1 {
            font-size: 2.25rem;
        }
        
        .app-header .subtitle {
            font-size: 1rem;
        }
        
        .glass-card {
            padding: 1.25rem;
            border-radius: 20px;
        }
        
        .verdict-icon {
            font-size: 3rem;
        }
        
        .verdict-text {
            font-size: 1.5rem;
        }
    }
    
    /* Summary card - Premium */
    .summary-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.02), rgba(139, 92, 246, 0.08), rgba(6, 182, 212, 0.05));
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 24px;
        padding: 2rem;
        margin-top: 1rem;
        position: relative;
        overflow: hidden;
    }
    
    .summary-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.05) 0%, transparent 50%);
        animation: aurora 15s ease-in-out infinite;
    }
    
    .summary-card p {
        color: var(--text-secondary);
        font-size: 1.1rem;
        line-height: 1.8;
        margin: 0;
        position: relative;
        z-index: 1;
    }
    
    /* Scrollbar styling - Premium */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--accent-primary), var(--accent-secondary));
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, var(--accent-secondary), var(--accent-tertiary));
    }
    
    /* Health Score Card - Premium Glassmorphism */
    .health-score-card {
        display: flex;
        align-items: center;
        gap: 2rem;
        background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(139, 92, 246, 0.1), rgba(6, 182, 212, 0.05));
        backdrop-filter: blur(20px);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 28px;
        padding: 2.5rem;
        animation: scaleIn 0.5s ease-out;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .health-score-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 30% 30%, rgba(139, 92, 246, 0.15), transparent 50%),
                    radial-gradient(circle at 70% 80%, rgba(6, 182, 212, 0.1), transparent 40%);
        pointer-events: none;
    }
    
    .health-score-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 20px 60px rgba(139, 92, 246, 0.25), 0 0 100px rgba(6, 182, 212, 0.1);
        border-color: rgba(6, 182, 212, 0.5);
    }
    
    .score-circle {
        width: 130px;
        height: 130px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        animation: pulse 3s ease-in-out infinite;
        box-shadow: 0 0 40px rgba(139, 92, 246, 0.3);
        z-index: 1;
    }
    
    .score-inner {
        width: 105px;
        height: 105px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--bg-primary), rgba(10, 10, 31, 0.95));
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: inset 0 0 30px rgba(139, 92, 246, 0.1);
    }
    
    .score-circle:hover .score-inner {
        transform: scale(1.08);
        box-shadow: inset 0 0 40px rgba(6, 182, 212, 0.2);
    }
    
    .score-grade {
        font-size: 2.75rem;
        font-weight: 900;
        line-height: 1;
        animation: fadeIn 0.5s ease-out 0.2s both;
        background: linear-gradient(135deg, #fff, var(--accent-primary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .score-value {
        font-size: 0.9rem;
        color: var(--text-muted);
        margin-top: 0.3rem;
    }
    
    .score-info {
        flex: 1;
        z-index: 1;
    }
    
    .score-label {
        font-size: 1.75rem;
        font-weight: 800;
        margin: 0;
        animation: slideInRight 0.5s ease-out;
        background: linear-gradient(135deg, #fff 0%, var(--accent-primary) 50%, var(--accent-secondary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    .score-subtitle {
        color: var(--text-secondary);
        font-size: 1rem;
        margin: 0.35rem 0 0 0;
    }
    
    /* Stat Cards - Premium with Gradient Borders */
    .stat-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 20px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        animation: fadeInUp 0.5s ease-out both;
        position: relative;
        overflow: hidden;
    }
    
    .stat-card::after {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, transparent, rgba(139, 92, 246, 0.05), rgba(6, 182, 212, 0.03));
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .stat-card:nth-child(1) { animation-delay: 0.1s; }
    .stat-card:nth-child(2) { animation-delay: 0.2s; }
    .stat-card:nth-child(3) { animation-delay: 0.3s; }
    .stat-card:nth-child(4) { animation-delay: 0.4s; }
    
    .stat-card:hover {
        border-color: rgba(6, 182, 212, 0.5);
        transform: translateY(-10px) scale(1.03);
        box-shadow: 0 20px 50px rgba(139, 92, 246, 0.25), 0 0 60px rgba(6, 182, 212, 0.1);
    }
    
    .stat-card:hover::after {
        opacity: 1;
    }
    
    .stat-value {
        font-size: 2.25rem;
        font-weight: 800;
        margin: 0;
        line-height: 1;
        transition: all 0.3s ease;
        position: relative;
        z-index: 1;
    }
    
    .stat-card:hover .stat-value {
        transform: scale(1.15);
    }
    
    .stat-label {
        color: var(--text-muted);
        font-size: 0.8rem;
        margin: 0.6rem 0 0 0;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        position: relative;
        z-index: 1;
    }
    
    /* History Card with slide animation */
    .history-card {
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        animation: fadeInUp 0.4s ease-out both;
        background: linear-gradient(135deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-radius: 18px;
        position: relative;
        overflow: hidden;
    }
    
    .history-card::before {
        content: '';
        position: absolute;
        inset: 0;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), rgba(6, 182, 212, 0.03));
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .history-card:hover {
        transform: translateX(8px) scale(1.01);
        border-color: rgba(6, 182, 212, 0.5);
        box-shadow: 0 10px 40px rgba(139, 92, 246, 0.2);
    }
    
    .history-card:hover::before {
        opacity: 1;
    }
    
    /* Interactive hover effects - Premium */
    .interactive-card {
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
    }
    
    .interactive-card::after {
        content: '';
        position: absolute;
        inset: -2px;
        border-radius: inherit;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(6, 182, 212, 0.3), rgba(244, 114, 182, 0.3));
        z-index: -1;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .interactive-card:hover {
        transform: translateY(-6px) scale(1.02);
        box-shadow: 0 25px 60px rgba(139, 92, 246, 0.25), 0 0 80px rgba(6, 182, 212, 0.1);
        border-color: transparent;
    }
    
    .interactive-card:hover::after {
        opacity: 1;
    }
    
    .interactive-card:active {
        transform: translateY(-3px) scale(1.01);
    }
    
    /* Pulse animation for active elements - Enhanced */
    .pulse-glow {
        animation: pulseGlow 2.5s ease-in-out infinite;
    }
    
    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 10px rgba(139, 92, 246, 0.3), 0 0 20px rgba(6, 182, 212, 0.1); }
        50% { box-shadow: 0 0 40px rgba(139, 92, 246, 0.5), 0 0 60px rgba(6, 182, 212, 0.3); }
    }
    
    /* Shimmer effect for loading states - Enhanced */
    .shimmer {
        background: linear-gradient(90deg, 
            rgba(139, 92, 246, 0.05) 0%, 
            rgba(6, 182, 212, 0.1) 25%,
            rgba(244, 114, 182, 0.08) 50%,
            rgba(6, 182, 212, 0.1) 75%,
            rgba(139, 92, 246, 0.05) 100%);
        background-size: 400% 100%;
        animation: shimmer 2s infinite linear;
    }
    
    @keyframes shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* Floating label effect - Enhanced */
    .floating-label {
        position: relative;
        overflow: hidden;
    }
    
    .floating-label::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary), var(--accent-tertiary));
        transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .floating-label:focus-within::after {
        width: 100%;
    }
    
    /* Tag/chip styles for ingredients - Premium */
    .ingredient-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.4rem 0.9rem;
        background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 25px;
        font-size: 0.82rem;
        color: var(--text-secondary);
        margin: 0.3rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        animation: fadeIn 0.3s ease-out both;
    }
    
    .ingredient-tag:hover {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(6, 182, 212, 0.05));
        border-color: var(--accent-secondary);
        color: var(--text-primary);
        transform: scale(1.08) translateY(-2px);
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.25);
    }
    
    .ingredient-tag:active {
        transform: scale(0.98);
    }
    
    .ingredient-tag.avoid {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(239, 68, 68, 0.05));
        border-color: rgba(239, 68, 68, 0.4);
        color: var(--danger);
        animation: shake 0.5s ease-out;
    }
    
    .ingredient-tag.watch {
        background: linear-gradient(135deg, rgba(234, 179, 8, 0.15), rgba(234, 179, 8, 0.05));
        border-color: rgba(234, 179, 8, 0.4);
        color: var(--warning);
        animation: pulse 2.5s ease-in-out infinite;
    }
    
    .ingredient-tag .remove {
        cursor: pointer;
        opacity: 0.6;
        transition: all 0.3s ease;
    }
    
    .ingredient-tag .remove:hover {
        opacity: 1;
        transform: rotate(180deg) scale(1.2);
    }
    
    /* Profile card - Premium Glassmorphism */
    .profile-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(139, 92, 246, 0.05), rgba(6, 182, 212, 0.02));
        backdrop-filter: blur(15px);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 24px;
        padding: 1.75rem;
        margin-bottom: 1rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        animation: fadeInUp 0.5s ease-out both;
    }
    
    .profile-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary), var(--accent-tertiary));
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .profile-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.08), rgba(6, 182, 212, 0.05), transparent);
        transition: left 0.6s ease;
    }
    
    .profile-card:hover {
        border-color: rgba(6, 182, 212, 0.5);
        transform: translateY(-6px);
        box-shadow: 0 20px 60px rgba(139, 92, 246, 0.2), 0 0 80px rgba(6, 182, 212, 0.1);
    }
    
    .profile-card:hover::before {
        opacity: 1;
    }
    
    .profile-card:hover::after {
        left: 100%;
    }
    
    .profile-card.active {
        border-color: var(--accent-primary);
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.08), rgba(99, 102, 241, 0.05));
        animation: borderGlow 2s ease-in-out infinite;
    }
    
    .profile-card.active::before {
        opacity: 1;
    }
    
    /* Severity badges with animations */
    .severity-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.25rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        animation: scaleIn 0.3s ease-out;
        transition: all 0.2s ease;
    }
    
    .severity-badge:hover {
        transform: scale(1.1);
    }
    
    .severity-badge.low {
        background: var(--success-soft);
        color: var(--success);
    }
    
    .severity-badge.medium {
        background: var(--warning-soft);
        color: var(--warning);
    }
    
    .severity-badge.high {
        background: var(--danger-soft);
        color: var(--danger);
    }
    
    /* Accordion/expandable styles with smooth animation */
    .expand-section {
        max-height: 0;
        overflow: hidden;
        transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .expand-section.expanded {
        max-height: 500px;
    }
    
    /* Icon button with micro-interactions */
    .icon-btn {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        color: var(--text-muted);
        position: relative;
        overflow: hidden;
    }
    
    .icon-btn::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        background: rgba(168, 85, 247, 0.2);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        transition: width 0.3s ease, height 0.3s ease;
    }
    
    .icon-btn:hover {
        background: var(--bg-card-hover);
        border-color: var(--accent-primary);
        color: var(--accent-primary);
        transform: scale(1.1);
    }
    
    .icon-btn:hover::before {
        width: 150%;
        height: 150%;
    }
    
    .icon-btn:active {
        transform: scale(0.95);
    }
    
    .icon-btn.danger:hover {
        border-color: var(--danger);
        color: var(--danger);
        background: var(--danger-soft);
    }
    
    .icon-btn.danger:hover::before {
        background: rgba(239, 68, 68, 0.2);
    }
    
    /* Quick action buttons with stagger */
    .quick-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
    }
    
    .quick-actions > * {
        animation: fadeInUp 0.3s ease-out both;
    }
    
    .quick-actions > *:nth-child(1) { animation-delay: 0.1s; }
    .quick-actions > *:nth-child(2) { animation-delay: 0.2s; }
    .quick-actions > *:nth-child(3) { animation-delay: 0.3s; }
    
    /* Empty state with floating animation */
    .empty-state {
        text-align: center;
        padding: 3rem 2rem;
        animation: fadeIn 0.5s ease-out;
    }
    
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        opacity: 0.3;
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    /* Tooltip with animation */
    .tooltip {
        position: relative;
    }
    
    .tooltip::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%) translateY(5px);
        padding: 0.5rem 0.75rem;
        background: var(--bg-secondary);
        border: 1px solid var(--border-subtle);
        border-radius: 8px;
        font-size: 0.75rem;
        color: var(--text-primary);
        white-space: nowrap;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .tooltip:hover::after {
        opacity: 1;
        visibility: visible;
        transform: translateX(-50%) translateY(-5px);
    }
    
    /* Counter badge with bounce animation */
    .counter-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 20px;
        height: 20px;
        padding: 0 6px;
        background: var(--accent-primary);
        color: white;
        border-radius: 10px;
        font-size: 0.7rem;
        font-weight: 600;
        animation: bounceIn 0.4s ease-out;
    }
    
    /* Confetti effect for good results */
    .confetti-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
        overflow: hidden;
    }
    
    .confetti {
        position: absolute;
        width: 10px;
        height: 10px;
        animation: confetti-fall 3s linear forwards;
    }
    
    @keyframes confetti-fall {
        0% {
            transform: translateY(-100px) rotate(0deg);
            opacity: 1;
        }
        100% {
            transform: translateY(100vh) rotate(720deg);
            opacity: 0;
        }
    }
    
    /* Typewriter effect for text */
    .typewriter {
        overflow: hidden;
        border-right: 2px solid var(--accent-primary);
        white-space: nowrap;
        animation: typing 2s steps(30, end), blink-caret 0.75s step-end infinite;
    }
    
    @keyframes typing {
        from { width: 0; }
        to { width: 100%; }
    }
    
    @keyframes blink-caret {
        from, to { border-color: transparent; }
        50% { border-color: var(--accent-primary); }
    }
    
    /* Progress ring animation */
    .progress-ring {
        transform: rotate(-90deg);
    }
    
    .progress-ring-circle {
        stroke-dasharray: 283;
        stroke-dashoffset: 283;
        animation: progress-fill 1.5s ease-out forwards;
    }
    
    @keyframes progress-fill {
        to { stroke-dashoffset: var(--progress-offset, 0); }
    }
    
    /* Success celebration animation */
    .celebrate {
        animation: celebrate 0.6s ease-out;
    }
    
    @keyframes celebrate {
        0% { transform: scale(1); }
        25% { transform: scale(1.2); }
        50% { transform: scale(0.95); }
        75% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-secondary) !important;
        justify-content: flex-start !important;
        padding-left: 1rem !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: var(--bg-card) !important;
        border-color: var(--accent-primary) !important;
        color: var(--text-primary) !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
        border: none !important;
        color: white !important;
    }
    
    /* Mobile health score */
    @media (max-width: 768px) {
        .health-score-card {
            flex-direction: column;
            text-align: center;
            gap: 1rem;
            padding: 1.5rem;
        }
        
        .score-circle {
            width: 100px;
            height: 100px;
        }
        
        .score-inner {
            width: 80px;
            height: 80px;
        }
        
        .score-grade {
            font-size: 2rem;
        }
    }
    
    /* 3D Canvas container */
    #three-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
        opacity: 0.8;
    }
    
    .stApp > div {
        position: relative;
        z-index: 1;
    }
    
    /* Animated gradient orbs - CSS only for Streamlit compatibility */
    .orb-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
        overflow: hidden;
    }
    
    .orb {
        position: absolute;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.6;
        animation: float 20s ease-in-out infinite;
    }
    
    .orb-1 {
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(168, 85, 247, 0.4) 0%, transparent 70%);
        top: -100px;
        right: -100px;
        animation-delay: 0s;
    }
    
    .orb-2 {
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(6, 182, 212, 0.35) 0%, transparent 70%);
        bottom: -50px;
        left: -100px;
        animation-delay: -5s;
        animation-duration: 25s;
    }
    
    .orb-3 {
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(244, 114, 182, 0.3) 0%, transparent 70%);
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        animation-delay: -10s;
        animation-duration: 30s;
    }
    
    .orb-4 {
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.5) 0%, transparent 70%);
        top: 30%;
        right: 20%;
        animation-delay: -15s;
        animation-duration: 22s;
    }
    
    .orb-5 {
        width: 350px;
        height: 350px;
        background: radial-gradient(circle, rgba(6, 182, 212, 0.25) 0%, transparent 70%);
        bottom: 20%;
        right: -80px;
        animation-delay: -8s;
        animation-duration: 28s;
    }
    
    @keyframes float {
        0%, 100% {
            transform: translate(0, 0) scale(1);
        }
        25% {
            transform: translate(50px, -40px) scale(1.1);
        }
        50% {
            transform: translate(-30px, 30px) scale(0.9);
        }
        75% {
            transform: translate(-40px, -30px) scale(1.05);
        }
    }
    
    /* Animated mesh grid - Premium */
    .mesh-grid {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            linear-gradient(rgba(139, 92, 246, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(6, 182, 212, 0.03) 1px, transparent 1px);
        background-size: 60px 60px;
        pointer-events: none;
        z-index: 0;
        animation: gridPulse 8s ease-in-out infinite;
    }
    
    @keyframes gridPulse {
        0%, 100% { opacity: 0.4; background-size: 60px 60px; }
        50% { opacity: 0.7; background-size: 65px 65px; }
    }
    
    /* Floating particles using pseudo-elements - Premium */
    .particles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
    }
    
    .particle {
        position: absolute;
        width: 5px;
        height: 5px;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.8), rgba(6, 182, 212, 0.6));
        border-radius: 50%;
        animation: particleFloat 15s linear infinite;
        box-shadow: 0 0 10px rgba(139, 92, 246, 0.5);
    }
    
    .particle:nth-child(1) { left: 10%; animation-duration: 20s; animation-delay: 0s; }
    .particle:nth-child(2) { left: 20%; animation-duration: 25s; animation-delay: -5s; }
    .particle:nth-child(3) { left: 30%; animation-duration: 18s; animation-delay: -2s; }
    .particle:nth-child(4) { left: 40%; animation-duration: 22s; animation-delay: -8s; }
    .particle:nth-child(5) { left: 50%; animation-duration: 28s; animation-delay: -3s; }
    .particle:nth-child(6) { left: 60%; animation-duration: 19s; animation-delay: -12s; }
    .particle:nth-child(7) { left: 70%; animation-duration: 24s; animation-delay: -7s; }
    .particle:nth-child(8) { left: 80%; animation-duration: 21s; animation-delay: -4s; }
    .particle:nth-child(9) { left: 90%; animation-duration: 26s; animation-delay: -10s; }
    .particle:nth-child(10) { left: 15%; animation-duration: 23s; animation-delay: -6s; }
    .particle:nth-child(11) { left: 35%; animation-duration: 27s; animation-delay: -9s; }
    .particle:nth-child(12) { left: 55%; animation-duration: 20s; animation-delay: -1s; }
    .particle:nth-child(13) { left: 75%; animation-duration: 24s; animation-delay: -11s; }
    .particle:nth-child(14) { left: 85%; animation-duration: 19s; animation-delay: -14s; }
    .particle:nth-child(15) { left: 5%; animation-duration: 22s; animation-delay: -13s; }
    
    @keyframes particleFloat {
        0% {
            transform: translateY(100vh) scale(0);
            opacity: 0;
        }
        10% {
            opacity: 1;
        }
        90% {
            opacity: 1;
        }
        100% {
            transform: translateY(-100vh) scale(1);
            opacity: 0;
        }
    }
    
    /* Glowing cursor trail effect via CSS - Enhanced */
    .glow-effect {
        position: fixed;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, 
            rgba(139, 92, 246, 0.2) 0%, 
            rgba(6, 182, 212, 0.1) 30%,
            transparent 70%);
        border-radius: 50%;
        pointer-events: none;
        z-index: 0;
        filter: blur(60px);
        animation: glowPulse 5s ease-in-out infinite;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }
    
    @keyframes glowPulse {
        0%, 100% { 
            opacity: 0.4; 
            transform: translate(-50%, -50%) scale(1) rotate(0deg);
        }
        25% {
            opacity: 0.6;
            transform: translate(-45%, -55%) scale(1.15) rotate(90deg);
        }
        50% { 
            opacity: 0.8; 
            transform: translate(-55%, -45%) scale(1.3) rotate(180deg);
        }
        75% {
            opacity: 0.5;
            transform: translate(-50%, -50%) scale(1.1) rotate(270deg);
        }
    }
    
    /* Aurora effect */
    .aurora {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 50%;
        background: linear-gradient(180deg,
            rgba(139, 92, 246, 0.15) 0%,
            rgba(6, 182, 212, 0.1) 30%,
            rgba(244, 114, 182, 0.05) 60%,
            transparent 100%);
        pointer-events: none;
        z-index: 0;
        animation: auroraWave 10s ease-in-out infinite;
    }
    
    @keyframes auroraWave {
        0%, 100% {
            opacity: 0.5;
            transform: translateY(0) scaleY(1);
        }
        50% {
            opacity: 0.8;
            transform: translateY(-20px) scaleY(1.1);
        }
    }
</style>
""", unsafe_allow_html=True)


# Premium animated background elements
def render_animated_background():
    """Render premium animated background with orbs, particles, grid, and aurora."""
    st.markdown("""
    <div class="aurora"></div>
    <div class="orb-container">
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
        <div class="orb orb-4"></div>
        <div class="orb orb-5"></div>
    </div>
    <div class="mesh-grid"></div>
    <div class="particles">
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
    </div>
    <div class="glow-effect"></div>
    """, unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'selected_profiles' not in st.session_state:
        st.session_state.selected_profiles = []
    if 'ingredients_input' not in st.session_state:
        st.session_state.ingredients_input = ""
    if 'show_camera' not in st.session_state:
        st.session_state.show_camera = False
    if 'extracted_text' not in st.session_state:
        st.session_state.extracted_text = ""
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "scan"
    # New hackathon features
    if 'scan_history' not in st.session_state:
        st.session_state.scan_history = []
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = []
    if 'show_onboarding' not in st.session_state:
        st.session_state.show_onboarding = True
    if 'comparison_mode' not in st.session_state:
        st.session_state.comparison_mode = False
    if 'comparison_results' not in st.session_state:
        st.session_state.comparison_results = []
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "main"
    # Custom profiles feature
    if 'custom_profiles' not in st.session_state:
        st.session_state.custom_profiles = []
    if 'selected_custom_profiles' not in st.session_state:
        st.session_state.selected_custom_profiles = []


def add_to_history(ingredients: str, result: Any, profiles: List):
    """Add a scan to history."""
    scan_id = hashlib.md5(f"{ingredients}{datetime.now()}".encode()).hexdigest()[:8]
    history_item = {
        "id": scan_id,
        "timestamp": datetime.now().isoformat(),
        "ingredients_preview": ingredients[:100] + "..." if len(ingredients) > 100 else ingredients,
        "verdict": result.overall_verdict,
        "confidence": result.confidence_score,
        "risk_count": len(result.risk_flags),
        "profiles": [p.value for p in profiles],
        "full_ingredients": ingredients
    }
    st.session_state.scan_history.insert(0, history_item)
    # Keep only last 20 scans
    st.session_state.scan_history = st.session_state.scan_history[:20]


def render_onboarding():
    """Render first-time user onboarding with premium eye-catching design."""
    
    # Hero Section
    st.markdown("""
    <style>
        .hero-section {
            text-align: center;
            padding: 3.5rem 1rem 2.5rem 1rem;
            animation: fadeIn 0.8s ease-out;
            position: relative;
        }
        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.6rem;
            padding: 0.6rem 1.25rem;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(6, 182, 212, 0.1));
            border: 1px solid rgba(139, 92, 246, 0.4);
            border-radius: 50px;
            color: #8b5cf6;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 1.75rem;
            animation: fadeInDown 0.6s ease-out, borderGlow 3s ease-in-out infinite;
        }
        .hero-title {
            font-size: 3.25rem;
            font-weight: 900;
            line-height: 1.05;
            margin: 0 0 1.25rem 0;
            background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 50%, #d0d0d0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: fadeInUp 0.6s ease-out 0.1s both;
            letter-spacing: -0.03em;
        }
        .hero-title span {
            background: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 50%, #f472b6 100%);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: textGradient 4s ease infinite;
        }
        .hero-subtitle {
            font-size: 1.2rem;
            color: rgba(255,255,255,0.75);
            line-height: 1.7;
            max-width: 550px;
            margin: 0 auto 2.5rem auto;
            animation: fadeInUp 0.6s ease-out 0.2s both;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.25rem;
            margin: 2.5rem 0;
        }
        .feature-item {
            background: linear-gradient(135deg, rgba(255,255,255,0.03), rgba(139, 92, 246, 0.05));
            border: 1px solid rgba(139, 92, 246, 0.2);
            border-radius: 20px;
            padding: 2rem 1.25rem;
            text-align: center;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            animation: fadeInUp 0.5s ease-out both;
            position: relative;
            overflow: hidden;
        }
        .feature-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, var(--accent-primary), var(--accent-secondary), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .feature-item:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: rgba(6, 182, 212, 0.5);
            box-shadow: 0 20px 50px rgba(139, 92, 246, 0.2), 0 0 80px rgba(6, 182, 212, 0.1);
        }
        .feature-item:hover::before {
            opacity: 1;
        }
        .feature-item:nth-child(1) { animation-delay: 0.1s; }
        .feature-item:nth-child(2) { animation-delay: 0.2s; }
        .feature-item:nth-child(3) { animation-delay: 0.3s; }
        .feature-icon-wrap {
            width: 56px;
            height: 56px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.25rem auto;
            font-size: 1.75rem;
            transition: all 0.3s ease;
        }
        .feature-item:hover .feature-icon-wrap {
            transform: scale(1.15);
        }
        .feature-icon-wrap.purple { 
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(139, 92, 246, 0.1)); 
            box-shadow: 0 8px 25px rgba(139, 92, 246, 0.3);
        }
        .feature-icon-wrap.pink { 
            background: linear-gradient(135deg, rgba(244, 114, 182, 0.25), rgba(244, 114, 182, 0.1)); 
            box-shadow: 0 8px 25px rgba(244, 114, 182, 0.3);
        }
        .feature-icon-wrap.blue { 
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.25), rgba(6, 182, 212, 0.1)); 
            box-shadow: 0 8px 25px rgba(6, 182, 212, 0.3);
        }
        .feature-title {
            color: var(--text-primary);
            font-weight: 700;
            font-size: 1.1rem;
            margin: 0 0 0.6rem 0;
        }
        .feature-desc {
            color: rgba(255,255,255,0.6);
            font-size: 0.9rem;
            margin: 0;
            line-height: 1.5;
        }
        .how-it-works {
            margin: 3.5rem 0 2.5rem 0;
            animation: fadeInUp 0.6s ease-out 0.4s both;
        }
        .how-title {
            text-align: center;
            color: var(--text-primary);
            font-size: 1.75rem;
            font-weight: 800;
            margin-bottom: 2.5rem;
            background: linear-gradient(135deg, #fff, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .steps-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 2rem;
        }
        .step-item {
            text-align: center;
            position: relative;
            animation: fadeInUp 0.5s ease-out both;
        }
        .step-item:nth-child(1) { animation-delay: 0.1s; }
        .step-item:nth-child(2) { animation-delay: 0.2s; }
        .step-item:nth-child(3) { animation-delay: 0.3s; }
        .step-number {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, #8b5cf6, #06b6d4);
            color: white;
            font-weight: 800;
            font-size: 1.25rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.25rem auto;
            box-shadow: 0 8px 30px rgba(139, 92, 246, 0.4);
            transition: all 0.3s ease;
        }
        .step-item:hover .step-number {
            transform: scale(1.15);
            box-shadow: 0 12px 40px rgba(6, 182, 212, 0.5);
        }
        .step-title {
            color: var(--text-primary);
            font-weight: 700;
            font-size: 1.1rem;
            margin: 0 0 0.6rem 0;
        }
        .step-desc {
            color: rgba(255,255,255,0.65);
            font-size: 0.9rem;
            line-height: 1.6;
            margin: 0;
        }
        .profiles-section {
            margin-top: 2.5rem;
            animation: fadeInUp 0.6s ease-out 0.5s both;
        }
        .profile-badge {
            padding: 0.5rem 1rem;
            border-radius: 25px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
            animation: scaleIn 0.4s ease-out both;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: default;
            margin: 0.25rem;
        }
        .profile-badge:hover {
            transform: scale(1.1) translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }
        @media (max-width: 768px) {
            .hero-title { font-size: 2.25rem; }
            .feature-grid { grid-template-columns: 1fr; }
            .steps-grid { grid-template-columns: 1fr; gap: 1.5rem; }
        }
    </style>
    
    <div class="hero-section">
        <div class="hero-badge">
            <span>🔬</span> AI-Powered Ingredient Analysis
        </div>
        <h1 class="hero-title">
            Know What's <span>Really</span><br>In Your Food
        </h1>
        <p class="hero-subtitle">
            Upload any nutrition label and get instant AI analysis of every ingredient.
            Personalized insights based on your health conditions.
        </p>
    </div>
    
    <!-- Feature Cards -->
    <div class="feature-grid">
        <div class="feature-item">
            <div class="feature-icon-wrap purple">⚡</div>
            <p class="feature-title">Instant Analysis</p>
            <p class="feature-desc">AI-powered results in seconds</p>
        </div>
        <div class="feature-item">
            <div class="feature-icon-wrap pink">🛡️</div>
            <p class="feature-title">Risk Detection</p>
            <p class="feature-desc">Identify harmful additives & allergens</p>
        </div>
        <div class="feature-item">
            <div class="feature-icon-wrap blue">🎯</div>
            <p class="feature-title">Personalized</p>
            <p class="feature-desc">Tailored to your health profile</p>
        </div>
    </div>
    
    <!-- How It Works -->
    <div class="how-it-works">
        <h2 class="how-title">How It Works</h2>
        <div class="steps-grid">
            <div class="step-item">
                <div class="step-number">1</div>
                <p class="step-title">Upload</p>
                <p class="step-desc">Take a photo of any nutrition label or ingredient list</p>
            </div>
            <div class="step-item">
                <div class="step-number">2</div>
                <p class="step-title">Analyze</p>
                <p class="step-desc">Our AI scans and identifies every ingredient instantly</p>
            </div>
            <div class="step-item">
                <div class="step-number">3</div>
                <p class="step-title">Understand</p>
                <p class="step-desc">Get personalized insights and smart recommendations</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Supported conditions
    st.markdown("""
    <div class="profiles-section">
        <div class="glass-card">
            <p style="color: var(--text-primary); font-weight: 700; font-size: 1.15rem; margin-bottom: 1.25rem; text-align: center;">
                ✨ 15 Supported Health Profiles
            </p>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center;">
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(239, 68, 68, 0.1)); border: 1px solid rgba(239, 68, 68, 0.4); color: #ef4444;">Diabetes</span>
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(234, 179, 8, 0.2), rgba(234, 179, 8, 0.1)); border: 1px solid rgba(234, 179, 8, 0.4); color: #eab308;">PCOS</span>
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(139, 92, 246, 0.1)); border: 1px solid rgba(139, 92, 246, 0.4); color: #8b5cf6;">Hypertension</span>
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(6, 182, 212, 0.1)); border: 1px solid rgba(6, 182, 212, 0.4); color: #06b6d4;">IBS</span>
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(34, 197, 94, 0.1)); border: 1px solid rgba(34, 197, 94, 0.4); color: #22c55e;">Celiac</span>
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(244, 114, 182, 0.2), rgba(244, 114, 182, 0.1)); border: 1px solid rgba(244, 114, 182, 0.4); color: #f472b6;">Nut Allergy</span>
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(14, 165, 233, 0.2), rgba(14, 165, 233, 0.1)); border: 1px solid rgba(14, 165, 233, 0.4); color: #0ea5e9;">Kidney</span>
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(34, 197, 94, 0.1)); border: 1px solid rgba(34, 197, 94, 0.4); color: #22c55e;">Keto</span>
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(139, 92, 246, 0.1)); border: 1px solid rgba(139, 92, 246, 0.4); color: #8b5cf6;">Thyroid</span>
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(244, 63, 94, 0.2), rgba(244, 63, 94, 0.1)); border: 1px solid rgba(244, 63, 94, 0.4); color: #f43f5e;">Heart</span>
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(6, 182, 212, 0.1)); border: 1px solid rgba(6, 182, 212, 0.4); color: #06b6d4;">Lactose</span>
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(234, 179, 8, 0.2), rgba(234, 179, 8, 0.1)); border: 1px solid rgba(234, 179, 8, 0.4); color: #eab308;">Gout</span>
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(249, 115, 22, 0.2), rgba(249, 115, 22, 0.1)); border: 1px solid rgba(249, 115, 22, 0.4); color: #f97316;">Fatty Liver</span>
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(132, 204, 22, 0.2), rgba(132, 204, 22, 0.1)); border: 1px solid rgba(132, 204, 22, 0.4); color: #84cc16;">GERD</span>
                <span class="profile-badge" style="background: linear-gradient(135deg, rgba(251, 146, 60, 0.2), rgba(251, 146, 60, 0.1)); border: 1px solid rgba(251, 146, 60, 0.4); color: #fb923c;">Seed Oil Free</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)
    
    if st.button("🚀 Get Started", type="primary", use_container_width=True):
        st.session_state.show_onboarding = False
        st.rerun()

def render_header():
    """Render the app header matching NutriScan style with premium effects."""
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 0 1.75rem 0; animation: fadeIn 0.6s ease-out;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #8b5cf6, #06b6d4, #f472b6); border-radius: 14px; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 30px rgba(139, 92, 246, 0.4); animation: pulse 3s ease-in-out infinite;">
                <span style="font-size: 1.5rem; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">🔍</span>
            </div>
            <span style="font-size: 1.5rem; font-weight: 800; background: linear-gradient(135deg, #fff, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.02em;">LabelLens</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 1rem; background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: 30px;">
            <span style="font-size: 0.8rem; color: rgba(255,255,255,0.7);">⚡ Powered by</span>
            <span style="font-size: 0.8rem; font-weight: 600; color: #8b5cf6;">Groq AI</span>
        </div>
    </div>
    
    <div style="text-align: center; padding: 1.5rem 0 2.5rem 0; animation: fadeInUp 0.6s ease-out 0.2s both;">
        <h1 style="font-size: 2.5rem; font-weight: 900; color: var(--text-primary); margin: 0 0 0.75rem 0; line-height: 1.15; letter-spacing: -0.03em;">
            Know What's <span style="background: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 50%, #f472b6 100%); background-size: 200% 200%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: textGradient 4s ease infinite;">Really</span> In Your Food
        </h1>
        <p style="color: var(--text-secondary); font-size: 1.1rem; margin: 0; opacity: 0.9;">
            AI-powered ingredient analysis personalized for your health
        </p>
        <div style="margin-top: 1.25rem; display: inline-flex; align-items: center; gap: 1.5rem;">
            <span style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.85rem; color: rgba(255,255,255,0.6);">
                <span style="color: #22c55e;">✓</span> Instant Analysis
            </span>
            <span style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.85rem; color: rgba(255,255,255,0.6);">
                <span style="color: #22c55e;">✓</span> 15+ Health Profiles
            </span>
            <span style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.85rem; color: rgba(255,255,255,0.6);">
                <span style="color: #22c55e;">✓</span> Camera Scan
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_profile_selector() -> UserProfile:
    """Render the health profile selector with a clean dropdown style."""
    
    st.markdown("""
    <div class="glass-card" style="animation: fadeInUp 0.4s ease-out;">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.25rem;">
            <div style="width: 44px; height: 44px; background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(6, 182, 212, 0.15)); border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 20px rgba(139, 92, 246, 0.2);">
                <span style="font-size: 1.25rem;">❤️</span>
            </div>
            <div>
                <p style="color: var(--text-primary); font-weight: 700; margin: 0; font-size: 1.1rem;">Health Profile</p>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin: 0;">Select your conditions for personalized analysis</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    available_profiles = get_available_profiles()
    
    # Get current selections
    if 'selected_profile_types' not in st.session_state:
        st.session_state.selected_profile_types = []
    
    # Create columns for profile chips
    cols = st.columns(3)
    selected_types = []
    
    for i, (display_name, profile_type) in enumerate(available_profiles.items()):
        with cols[i % 3]:
            is_selected = st.checkbox(
                display_name,
                key=f"profile_{profile_type.value}",
                value=profile_type in st.session_state.selected_profile_types
            )
            if is_selected:
                selected_types.append(profile_type)
    
    st.session_state.selected_profile_types = selected_types
    
    # Show custom profiles if any are active
    active_custom = [p for p in st.session_state.custom_profiles if p['id'] in st.session_state.selected_custom_profiles]
    
    # Show selected count
    total_selected = len(selected_types) + len(active_custom)
    if total_selected > 0:
        custom_text = f" + {len(active_custom)} custom" if active_custom else ""
        st.markdown(f"""
        <div style="margin-top: 1rem; padding: 0.75rem 1rem; background: var(--success-soft); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px;">
            <p style="margin: 0; color: var(--success); font-weight: 500; font-size: 0.9rem;">✓ {len(selected_types)} profile(s) selected{custom_text}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="margin-top: 1rem; padding: 0.75rem 1rem; background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: 12px;">
            <p style="margin: 0; color: var(--text-muted); font-size: 0.9rem;">Select your health conditions above</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Link to custom profiles
    if st.session_state.custom_profiles:
        st.markdown(f"""
        <div style="margin-top: 0.5rem; text-align: center;">
            <p style="color: var(--text-muted); font-size: 0.8rem; margin: 0;">
                {len(active_custom)}/{len(st.session_state.custom_profiles)} custom profiles active
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Button to manage custom profiles
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🏷️ Manage Custom Profiles", use_container_width=True):
            st.session_state.current_view = "custom_profiles"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Build custom restrictions from active custom profiles
    custom_restrictions = []
    for profile in active_custom:
        avoid_str = ", ".join(profile.get("avoid", []))
        watch_str = ", ".join(profile.get("watch", []))
        restriction = f"{profile['name']}: Avoid [{avoid_str}]"
        if watch_str:
            restriction += f", Watch [{watch_str}]"
        custom_restrictions.append(restriction)
    
    return UserProfile(active_profiles=selected_types, custom_restrictions=custom_restrictions)


def render_scan_section():
    """Render the camera/scan section matching NutriScan upload card style."""
    
    st.markdown("""
    <div class="glass-card" style="animation: fadeInUp 0.4s ease-out;">
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem;">
            <div style="width: 36px; height: 36px; background: rgba(236, 72, 153, 0.15); border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 1.1rem;">📷</span>
            </div>
            <div>
                <p style="color: var(--text-primary); font-weight: 600; margin: 0; font-size: 1rem;">Upload Product Image</p>
                <p style="color: var(--text-muted); font-size: 0.8rem; margin: 0;">Drag & drop or click to select</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs for Photo and Upload (like NutriScan's Photo/Barcode)
    tab1, tab2 = st.tabs(["📸 Camera", "📁 Upload"])
    
    with tab1:
        camera_image = st.camera_input(
            "Take a photo",
            key="camera",
            help="Point your camera at the ingredient list",
            label_visibility="collapsed"
        )
    
    with tab2:
        uploaded_file = st.file_uploader(
            "Upload image",
            type=['png', 'jpg', 'jpeg'],
            key="upload",
            label_visibility="collapsed"
        )
    
    # Process image if available
    image_to_process = camera_image or uploaded_file
    
    if image_to_process:
        # Show preview with animation
        st.markdown('<div style="animation: scaleIn 0.4s ease-out; margin: 1rem 0;">', unsafe_allow_html=True)
        st.image(image_to_process, caption="Captured Image", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("🔍 Extract Text", type="primary", use_container_width=True):
            # Custom loading for OCR
            loading_placeholder = st.empty()
            with loading_placeholder.container():
                st.markdown("""
                <div style="text-align: center; padding: 2rem; animation: fadeIn 0.3s ease-out;">
                    <div style="display: flex; justify-content: center; gap: 0.5rem; margin-bottom: 1rem;">
                        <div style="width: 10px; height: 10px; border-radius: 50%; background: var(--accent-primary); animation: loadingBounce 1.4s ease-in-out infinite;"></div>
                        <div style="width: 10px; height: 10px; border-radius: 50%; background: var(--accent-secondary); animation: loadingBounce 1.4s ease-in-out 0.16s infinite;"></div>
                        <div style="width: 10px; height: 10px; border-radius: 50%; background: var(--accent-tertiary); animation: loadingBounce 1.4s ease-in-out 0.32s infinite;"></div>
                    </div>
                    <p style="color: var(--text-primary); font-weight: 600; margin: 0;">Reading ingredients...</p>
                    <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.5rem;">AI is analyzing the image</p>
                </div>
                <style>
                    @keyframes loadingBounce {
                        0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
                        40% { transform: scale(1); opacity: 1; }
                    }
                </style>
                """, unsafe_allow_html=True)
            
            try:
                # Convert to bytes
                image_bytes = image_to_process.getvalue()
                
                # Extract text using EasyOCR
                extracted = extract_ingredients_from_image(image_bytes)
                loading_placeholder.empty()
                
                if extracted:
                    st.session_state.extracted_text = extracted
                    st.session_state.ingredients_input = extracted
                    st.rerun()
                else:
                    st.markdown("""
                    <div style="padding: 1rem; background: var(--danger-soft); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; margin-top: 1rem; animation: shake 0.5s ease-out;">
                        <p style="margin: 0; color: var(--danger); font-size: 0.9rem;">Could not extract text. Try a clearer photo.</p>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                loading_placeholder.empty()
                st.error(f"Error: {str(e)}")
    else:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
            <p style="font-size: 2.5rem; margin: 0; opacity: 0.5; animation: float 3s ease-in-out infinite;">📷</p>
            <p style="margin: 0.75rem 0 0 0; font-size: 0.9rem;">Capture or upload ingredient list</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_text_input():
    """Render the text input section matching NutriScan style."""
    
    st.markdown("""
    <div class="glass-card" style="animation: fadeInUp 0.4s ease-out 0.1s both;">
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <div style="width: 36px; height: 36px; background: rgba(99, 102, 241, 0.15); border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 1.1rem;">📝</span>
            </div>
            <div>
                <p style="color: var(--text-primary); font-weight: 600; margin: 0; font-size: 1rem;">Ingredients</p>
                <p style="color: var(--text-muted); font-size: 0.8rem; margin: 0;">Paste or type ingredient list</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    ingredients_input = st.text_area(
        "Ingredient list",
        value=st.session_state.get('extracted_text', ''),
        height=120,
        placeholder="Paste ingredients here...\n\nExample: Water, Sugar, Wheat Flour, Soybean Oil...",
        label_visibility="collapsed"
    )
    
    st.session_state.ingredients_input = ingredients_input
    
    # Quick samples
    st.markdown("<p style='font-size: 0.8rem; color: var(--text-muted); margin: 1rem 0 0.5rem 0;'>Try a sample:</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🍞 Bread", use_container_width=True, key="sample_bread"):
            st.session_state.ingredients_input = """Enriched Wheat Flour (Wheat Flour, Malted Barley Flour, Niacin, Iron, Thiamin Mononitrate, Riboflavin, Folic Acid), Water, High Fructose Corn Syrup, Yeast, Soybean Oil, Salt, Wheat Gluten, Calcium Sulfate, Sodium Stearoyl Lactylate, Monoglycerides, Calcium Propionate (Preservative), Datem, Soy Lecithin."""
            st.session_state.extracted_text = st.session_state.ingredients_input
            st.rerun()
    
    with col2:
        if st.button("💪 Protein Bar", use_container_width=True, key="sample_protein"):
            st.session_state.ingredients_input = """Protein Blend (Whey Protein Isolate, Milk Protein Isolate), Soluble Corn Fiber, Almonds, Water, Erythritol, Palm Kernel Oil, Cocoa (Processed with Alkali), Natural Flavors, Sunflower Lecithin, Salt, Stevia Extract, Monk Fruit Extract."""
            st.session_state.extracted_text = st.session_state.ingredients_input
            st.rerun()
    
    with col3:
        if st.button("⚡ Energy Drink", use_container_width=True, key="sample_energy"):
            st.session_state.ingredients_input = """Carbonated Water, Citric Acid, Taurine, Sodium Citrate, Natural Flavors, Caffeine, Sucralose, Potassium Sorbate (Preservative), Sodium Benzoate (Preservative), Niacinamide, Calcium Pantothenate, Pyridoxine HCl, Vitamin B12."""
            st.session_state.extracted_text = st.session_state.ingredients_input
            st.rerun()
    
    return ingredients_input


def render_loading_animation():
    """Render a custom loading animation."""
    st.markdown("""
    <div class="loading-container">
        <div class="loading-spinner">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
        <p class="loading-text">Analyzing ingredients...</p>
        <p class="loading-subtext">Checking against your health profiles</p>
    </div>
    <style>
        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 3rem;
            animation: fadeIn 0.3s ease-out;
        }
        .loading-spinner {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .loading-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            animation: loadingBounce 1.4s ease-in-out infinite both;
        }
        .loading-dot:nth-child(1) { animation-delay: 0s; }
        .loading-dot:nth-child(2) { animation-delay: 0.16s; }
        .loading-dot:nth-child(3) { animation-delay: 0.32s; }
        @keyframes loadingBounce {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }
        .loading-text {
            color: var(--text-primary);
            font-size: 1.1rem;
            font-weight: 600;
            margin: 0;
            animation: pulse 2s ease-in-out infinite;
        }
        .loading-subtext {
            color: var(--text-muted);
            font-size: 0.85rem;
            margin: 0.5rem 0 0 0;
        }
    </style>
    """, unsafe_allow_html=True)


def render_analyze_button(user_profile: UserProfile, ingredients: str):
    """Render the analyze button."""
    
    can_analyze = bool(ingredients and user_profile.active_profiles and GROQ_API_KEY)
    
    if st.button(
        "🔬 Analyze Ingredients",
        type="primary",
        use_container_width=True,
        disabled=not can_analyze
    ):
        if not GROQ_API_KEY:
            st.error("Groq API key not configured")
            return
        
        # Show custom loading animation
        loading_placeholder = st.empty()
        with loading_placeholder.container():
            render_loading_animation()
        
        try:
            result = analyze_ingredients(
                ingredients=ingredients,
                user_profile=user_profile,
                include_deception_check=True
            )
            loading_placeholder.empty()
            st.session_state.analysis_result = result
            st.rerun()
        except Exception as e:
            loading_placeholder.empty()
            st.error(f"Analysis failed: {str(e)}")
    
    if not ingredients:
        st.markdown("<p style='text-align: center; color: var(--text-muted); font-size: 0.85rem; margin-top: 0.75rem;'>Add ingredients above to analyze</p>", unsafe_allow_html=True)
    elif not user_profile.active_profiles:
        st.markdown("<p style='text-align: center; color: var(--text-muted); font-size: 0.85rem; margin-top: 0.75rem;'>Select at least one health profile</p>", unsafe_allow_html=True)


def render_verdict(result: AnalysisResult):
    """Render the verdict card with animations."""
    
    verdict_config = {
        Verdict.SAFE: {
            "class": "verdict-safe",
            "icon": "✓",
            "title": "ALL CLEAR",
            "subtitle": "This product looks safe for your health profiles",
            "animation": "celebrate"
        },
        Verdict.CAUTION: {
            "class": "verdict-caution",
            "icon": "!",
            "title": "CAUTION",
            "subtitle": "Review the concerns below before consuming",
            "animation": "pulse"
        },
        Verdict.AVOID: {
            "class": "verdict-avoid",
            "icon": "✕",
            "title": "AVOID",
            "subtitle": "This product is not recommended for you",
            "animation": "shake"
        }
    }
    
    config = verdict_config.get(result.overall_verdict, verdict_config[Verdict.CAUTION])
    
    st.markdown(f"""
    <style>
        .verdict-card-animated {{
            animation: scaleIn 0.5s ease-out;
        }}
        .verdict-icon-animated {{
            animation: {config['animation']} 0.6s ease-out;
        }}
        .verdict-title-animated {{
            animation: fadeInUp 0.5s ease-out 0.2s both;
        }}
        .verdict-subtitle-animated {{
            animation: fadeIn 0.5s ease-out 0.4s both;
        }}
    </style>
    <div class="{config['class']} verdict-card-animated">
        <div class="verdict-icon verdict-icon-animated">{config['icon']}</div>
        <p class="verdict-text verdict-title-animated">{config['title']}</p>
        <p class="verdict-subtitle verdict-subtitle-animated">{config['subtitle']}</p>
        <div style="margin-top: 1.5rem; animation: fadeIn 0.5s ease-out 0.6s both;">
            <span style="font-size: 0.85rem; color: rgba(255,255,255,0.8);">Confidence Score</span>
            <div class="confidence-meter">
                <div class="confidence-fill" style="width: {result.confidence_score * 100}%"></div>
            </div>
            <span style="font-size: 0.9rem; font-weight: 600; color: rgba(255,255,255,0.9);">{result.confidence_score:.0%}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary
    st.markdown(f"""
    <div class="summary-card">
        <p>{result.summary}</p>
    </div>
    """, unsafe_allow_html=True)


def render_risk_flags(result: AnalysisResult):
    """Render risk flags."""
    
    if not result.risk_flags:
        st.markdown("""
        <div class="glass-card" style="text-align: center;">
            <p style="font-size: 2.5rem; margin: 0;">✓</p>
            <p style="font-size: 1.1rem; color: var(--text-secondary); margin: 0.5rem 0 0 0;">No risks found for your profiles</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown('<div class="section-header">Risk Flags</div>', unsafe_allow_html=True)
    
    for flag in result.risk_flags:
        severity_class = f"risk-{flag.severity}"
        
        st.markdown(f"""
        <div class="risk-card {severity_class}">
            <div class="risk-header">
                {flag.ingredient}
                <span class="risk-badge">{flag.risk_type.replace('_', ' ')}</span>
            </div>
            <div class="risk-body">
                {flag.explanation}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_smart_swaps(result: AnalysisResult):
    """Render smart swap suggestions."""
    
    if not result.smart_swaps:
        return
    
    st.markdown('<div class="section-header">Smart Swaps</div>', unsafe_allow_html=True)
    
    for swap in result.smart_swaps:
        st.markdown(f"""
        <div class="swap-card">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="flex: 1; text-align: center;">
                    <p style="margin: 0; font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Avoid</p>
                    <p style="margin: 0.25rem 0; font-weight: 600; color: #ef4444; font-size: 1.05rem;">{swap.avoid}</p>
                </div>
                <div class="swap-arrow">→</div>
                <div style="flex: 1; text-align: center;">
                    <p style="margin: 0; font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Try</p>
                    <p style="margin: 0.25rem 0; font-weight: 600; color: #10b981; font-size: 1.05rem;">{swap.try_instead}</p>
                </div>
            </div>
            <p style="margin: 1rem 0 0 0; font-size: 0.9rem; color: var(--text-secondary); text-align: center; line-height: 1.5;">
                {swap.reason}
            </p>
        </div>
        """, unsafe_allow_html=True)


def render_deception_alerts(result: AnalysisResult):
    """Render deception alerts."""
    
    if not result.deception_alerts:
        return
    
    st.markdown('<div class="section-header">Reality Check</div>', unsafe_allow_html=True)
    
    for alert in result.deception_alerts:
        st.markdown(f"""
        <div class="glass-card" style="border-left: 3px solid var(--warning);">
            <p style="margin: 0; font-weight: 600; color: var(--text-primary);">
                Claim: "{alert.claim}"
            </p>
            <p style="margin: 0.75rem 0 0 0; color: var(--text-secondary); line-height: 1.5;">
                <span style="color: var(--success);">Reality:</span> {alert.reality}
            </p>
        </div>
        """, unsafe_allow_html=True)


def render_results(result: AnalysisResult):
    """Render the complete results section."""
    
    # Add to history
    if st.session_state.ingredients_input and 'history_added' not in st.session_state:
        add_to_history(
            st.session_state.ingredients_input, 
            result, 
            st.session_state.selected_profile_types
        )
        st.session_state.history_added = True
    
    # Health Score Card
    render_health_score(result)
    
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    
    # Verdict
    render_verdict(result)
    
    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
    
    # Quick Stats Row
    col1, col2, col3, col4 = st.columns(4)
    
    risk_count = len(result.risk_flags)
    critical_count = sum(1 for f in result.risk_flags if f.severity == "critical")
    swap_count = len(result.smart_swaps)
    deception_count = len(result.deception_alerts)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-value" style="color: {'var(--danger)' if risk_count > 0 else 'var(--success)'};">{risk_count}</p>
            <p class="stat-label">Risks Found</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-value" style="color: {'#ef4444' if critical_count > 0 else 'var(--text-muted)'};">{critical_count}</p>
            <p class="stat-label">Critical</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-value" style="color: var(--accent-primary);">{swap_count}</p>
            <p class="stat-label">Alternatives</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-value" style="color: {'var(--warning)' if deception_count > 0 else 'var(--text-muted)'};">{deception_count}</p>
            <p class="stat-label">Warnings</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Risks", "Alternatives", "Marketing"])
    
    with tab1:
        render_risk_flags(result)
    
    with tab2:
        if result.smart_swaps:
            render_smart_swaps(result)
        else:
            st.markdown("""
            <div class="glass-card" style="text-align: center;">
                <p style="font-size: 2rem; margin: 0;">✨</p>
                <p style="color: var(--text-secondary); margin: 0.5rem 0 0 0;">No alternatives needed</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab3:
        if result.deception_alerts:
            render_deception_alerts(result)
        else:
            st.markdown("""
            <div class="glass-card" style="text-align: center;">
                <p style="font-size: 2rem; margin: 0;">✓</p>
                <p style="color: var(--text-secondary); margin: 0.5rem 0 0 0;">No misleading claims detected</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Action buttons
    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        report_json = json.dumps(result.to_dict(), indent=2, default=str)
        st.download_button(
            "↓ Export",
            data=report_json,
            file_name="labellens_report.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        # Share button - generate shareable text
        share_text = f"🔍 LabelLens Analysis: {result.overall_verdict}\n"
        share_text += f"Found {risk_count} risks, {swap_count} alternatives suggested.\n"
        share_text += f"Confidence: {result.confidence_score:.0%}"
        
        st.download_button(
            "↗ Share",
            data=share_text,
            file_name="labellens_share.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col3:
        if st.button("← New Scan", use_container_width=True):
            st.session_state.analysis_result = None
            st.session_state.extracted_text = ""
            st.session_state.ingredients_input = ""
            if 'history_added' in st.session_state:
                del st.session_state.history_added
            st.rerun()


def render_health_score(result: AnalysisResult):
    """Render a visual health score with celebration effects."""
    # Calculate health score (0-100)
    base_score = 100
    
    # Deduct points based on risks
    for flag in result.risk_flags:
        if flag.severity == "critical":
            base_score -= 25
        elif flag.severity == "high":
            base_score -= 15
        elif flag.severity == "medium":
            base_score -= 8
        else:
            base_score -= 3
    
    # Deduct for deception
    base_score -= len(result.deception_alerts) * 5
    
    # Clamp to 0-100
    score = max(0, min(100, base_score))
    
    # Determine color based on score
    if score >= 80:
        color = "#10b981"
        grade = "A"
        label = "Excellent"
        show_confetti = True
    elif score >= 60:
        color = "#22c55e"
        grade = "B"
        label = "Good"
        show_confetti = False
    elif score >= 40:
        color = "#f59e0b"
        grade = "C"
        label = "Fair"
        show_confetti = False
    elif score >= 20:
        color = "#f97316"
        grade = "D"
        label = "Poor"
        show_confetti = False
    else:
        color = "#ef4444"
        grade = "F"
        label = "Avoid"
        show_confetti = False
    
    # Confetti for excellent scores
    confetti_html = ""
    if show_confetti:
        confetti_pieces = ""
        colors = ["#a855f7", "#ec4899", "#6366f1", "#10b981", "#f59e0b"]
        for i in range(30):
            left = (i * 3.33) % 100
            delay = (i * 0.1) % 2
            color_pick = colors[i % len(colors)]
            size = 6 + (i % 8)
            confetti_pieces += f'<div class="confetti" style="left: {left}%; animation-delay: {delay}s; background: {color_pick}; width: {size}px; height: {size}px; border-radius: {50 if i % 2 == 0 else 0}%;"></div>'
        confetti_html = f'<div class="confetti-container">{confetti_pieces}</div>'
    
    st.markdown(f"""
    {confetti_html}
    <div class="health-score-card celebrate">
        <div class="score-circle" style="background: conic-gradient({color} {score * 3.6}deg, rgba(255,255,255,0.1) 0deg);">
            <div class="score-inner">
                <span class="score-grade" style="color: {color};">{grade}</span>
                <span class="score-value">{score}</span>
            </div>
        </div>
        <div class="score-info">
            <p class="score-label" style="color: {color};">{label}</p>
            <p class="score-subtitle">Health Score for Your Profile</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_history():
    """Render scan history."""
    st.markdown("""
    <div class="app-header">
        <h1>Scan History</h1>
        <p class="subtitle">Your recent product analyses</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.scan_history:
        st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 3rem;">
            <p style="font-size: 3rem; margin: 0; opacity: 0.5;">📋</p>
            <p style="color: var(--text-secondary); margin: 1rem 0 0 0;">No scans yet</p>
            <p style="color: var(--text-muted); font-size: 0.9rem;">Start scanning products to build your history</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for item in st.session_state.scan_history:
            verdict_color = {
                "SAFE": "var(--success)",
                "CAUTION": "var(--warning)",
                "AVOID": "var(--danger)"
            }.get(item['verdict'], "var(--text-muted)")
            
            timestamp = datetime.fromisoformat(item['timestamp']).strftime("%b %d, %I:%M %p")
            
            st.markdown(f"""
            <div class="glass-card history-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="flex: 1;">
                        <p style="color: var(--text-primary); font-weight: 500; margin: 0; font-size: 0.95rem;">
                            {item['ingredients_preview']}
                        </p>
                        <p style="color: var(--text-muted); font-size: 0.8rem; margin: 0.5rem 0 0 0;">
                            {timestamp} · {item['risk_count']} risks
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <span style="padding: 0.35rem 0.75rem; background: {verdict_color}20; color: {verdict_color}; border-radius: 20px; font-size: 0.75rem; font-weight: 600;">
                            {item['verdict']}
                        </span>
                        <p style="color: var(--text-muted); font-size: 0.75rem; margin: 0.5rem 0 0 0;">
                            {item['confidence']:.0%} confidence
                        </p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Scanner", use_container_width=True):
            st.session_state.current_view = "main"
            st.rerun()
    with col2:
        if st.session_state.scan_history and st.button("Clear History", use_container_width=True):
            st.session_state.scan_history = []
            st.rerun()


def render_statistics():
    """Render user statistics dashboard."""
    st.markdown("""
    <div class="app-header">
        <h1>Your Insights</h1>
        <p class="subtitle">Analytics from your scanning activity</p>
    </div>
    """, unsafe_allow_html=True)
    
    history = st.session_state.scan_history
    
    if not history:
        st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 3rem;">
            <p style="font-size: 3rem; margin: 0; opacity: 0.5;">📊</p>
            <p style="color: var(--text-secondary); margin: 1rem 0 0 0;">No data yet</p>
            <p style="color: var(--text-muted); font-size: 0.9rem;">Scan products to see your insights</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Calculate statistics
        total_scans = len(history)
        safe_count = sum(1 for h in history if h['verdict'] == 'SAFE')
        caution_count = sum(1 for h in history if h['verdict'] == 'CAUTION')
        avoid_count = sum(1 for h in history if h['verdict'] == 'AVOID')
        avg_confidence = sum(h['confidence'] for h in history) / total_scans if total_scans else 0
        total_risks = sum(h['risk_count'] for h in history)
        
        # Stats cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <p style="font-size: 2.5rem; font-weight: 700; color: var(--accent-primary); margin: 0;">{total_scans}</p>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">Total Scans</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <p style="font-size: 2.5rem; font-weight: 700; color: var(--warning); margin: 0;">{total_risks}</p>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">Risks Detected</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <p style="font-size: 2.5rem; font-weight: 700; color: var(--success); margin: 0;">{avg_confidence:.0%}</p>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">Avg Confidence</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Verdict breakdown
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-card">
            <p style="color: var(--text-primary); font-weight: 600; margin-bottom: 1rem;">Verdict Breakdown</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Visual breakdown
        safe_pct = (safe_count / total_scans * 100) if total_scans else 0
        caution_pct = (caution_count / total_scans * 100) if total_scans else 0
        avoid_pct = (avoid_count / total_scans * 100) if total_scans else 0
        
        st.markdown(f"""
        <div class="glass-card">
            <div style="display: flex; height: 12px; border-radius: 6px; overflow: hidden; margin-bottom: 1rem;">
                <div style="width: {safe_pct}%; background: var(--success);"></div>
                <div style="width: {caution_pct}%; background: var(--warning);"></div>
                <div style="width: {avoid_pct}%; background: var(--danger);"></div>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: var(--success); font-size: 0.85rem;">✓ Safe: {safe_count}</span>
                <span style="color: var(--warning); font-size: 0.85rem;">! Caution: {caution_count}</span>
                <span style="color: var(--danger); font-size: 0.85rem;">✕ Avoid: {avoid_count}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    
    if st.button("← Back to Scanner", use_container_width=True):
        st.session_state.current_view = "main"
        st.rerun()


def render_custom_profiles():
    """Render custom health profiles management page with enhanced interactivity."""
    
    # Header with stats
    active_count = len(st.session_state.selected_custom_profiles)
    total_count = len(st.session_state.custom_profiles)
    
    st.markdown(f"""
    <div class="app-header" style="padding-bottom: 1.5rem;">
        <h1>Custom Profiles</h1>
        <p class="subtitle">Create personalized health profiles for precise ingredient analysis</p>
        <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 1.5rem;">
            <div style="text-align: center; padding: 0.75rem 1.5rem; background: var(--bg-card); border-radius: 16px; border: 1px solid var(--border-subtle);">
                <span style="font-size: 1.5rem; font-weight: 700; color: var(--accent-primary);">{total_count}</span>
                <p style="margin: 0; font-size: 0.8rem; color: var(--text-muted);">Profiles</p>
            </div>
            <div style="text-align: center; padding: 0.75rem 1.5rem; background: var(--bg-card); border-radius: 16px; border: 1px solid var(--border-subtle);">
                <span style="font-size: 1.5rem; font-weight: 700; color: var(--success);">{active_count}</span>
                <p style="margin: 0; font-size: 0.8rem; color: var(--text-muted);">Active</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs for Create / Manage
    tab_create, tab_manage, tab_templates = st.tabs(["➕ Create New", "📋 My Profiles", "🎯 Quick Templates"])
    
    with tab_create:
        st.markdown("""
        <div class="glass-card" style="margin-top: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem;">
                <span style="font-size: 1.5rem;">✨</span>
                <div>
                    <h3 style="color: var(--text-primary); margin: 0; font-size: 1.1rem;">Create Your Profile</h3>
                    <p style="color: var(--text-muted); margin: 0; font-size: 0.85rem;">Define ingredients that matter to your health</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Profile creation form with better UX
        col1, col2 = st.columns([2, 1])
        
        with col1:
            profile_name = st.text_input(
                "Profile Name *",
                placeholder="e.g., My Migraine Triggers, Low Histamine Diet",
                max_chars=50,
                help="Give your profile a memorable name"
            )
        
        with col2:
            profile_icon = st.selectbox(
                "Icon",
                options=["🏷️", "⚠️", "🚫", "💊", "🩺", "🧬", "🍎", "🌿", "❤️", "🧠", "🦴", "👁️"],
                help="Choose an icon for your profile"
            )
        
        profile_description = st.text_input(
            "Description (optional)",
            placeholder="Brief description of what this profile tracks...",
            max_chars=150
        )
        
        st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
        
        # Two columns for avoid and watch
        col_avoid, col_watch = st.columns(2)
        
        with col_avoid:
            st.markdown("""
            <div style="padding: 0.75rem; background: var(--danger-soft); border-radius: 12px; margin-bottom: 0.5rem;">
                <span style="color: var(--danger); font-weight: 600; font-size: 0.9rem;">🚫 Ingredients to AVOID</span>
                <p style="color: var(--text-muted); font-size: 0.75rem; margin: 0.25rem 0 0 0;">Will be flagged as dangerous</p>
            </div>
            """, unsafe_allow_html=True)
            avoid_ingredients = st.text_area(
                "Avoid list",
                placeholder="tyramine, MSG, nitrates, aged cheese...",
                height=120,
                label_visibility="collapsed",
                help="Separate ingredients with commas"
            )
        
        with col_watch:
            st.markdown("""
            <div style="padding: 0.75rem; background: var(--warning-soft); border-radius: 12px; margin-bottom: 0.5rem;">
                <span style="color: var(--warning); font-weight: 600; font-size: 0.9rem;">⚠️ Ingredients to WATCH</span>
                <p style="color: var(--text-muted); font-size: 0.75rem; margin: 0.25rem 0 0 0;">Will trigger caution alerts</p>
            </div>
            """, unsafe_allow_html=True)
            watch_ingredients = st.text_area(
                "Watch list",
                placeholder="caffeine, chocolate, citrus, alcohol...",
                height=120,
                label_visibility="collapsed",
                help="Separate ingredients with commas"
            )
        
        # Severity selector with visual feedback
        st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
        
        severity = st.radio(
            "Sensitivity Level",
            options=["Low", "Medium", "High"],
            horizontal=True,
            index=1,
            help="How strictly should this profile flag ingredients?"
        )
        
        # Preview of ingredients
        avoid_list = [i.strip().lower() for i in avoid_ingredients.split(",") if i.strip()]
        watch_list = [i.strip().lower() for i in watch_ingredients.split(",") if i.strip()]
        
        if avoid_list or watch_list:
            st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)
            st.markdown("""
            <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">Preview:</p>
            """, unsafe_allow_html=True)
            
            preview_html = '<div style="display: flex; flex-wrap: wrap; gap: 0.35rem;">'
            for ing in avoid_list[:10]:
                preview_html += f'<span class="ingredient-tag avoid">🚫 {ing}</span>'
            for ing in watch_list[:10]:
                preview_html += f'<span class="ingredient-tag watch">⚠️ {ing}</span>'
            if len(avoid_list) + len(watch_list) > 20:
                preview_html += f'<span class="ingredient-tag">+{len(avoid_list) + len(watch_list) - 20} more</span>'
            preview_html += '</div>'
            st.markdown(preview_html, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
        
        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✨ Create Profile", type="primary", use_container_width=True):
                if not profile_name.strip():
                    st.error("Please enter a profile name")
                elif not avoid_list and not watch_list:
                    st.error("Please add at least one ingredient to avoid or watch")
                else:
                    # Create profile object
                    new_profile = {
                        "id": f"custom_{len(st.session_state.custom_profiles)}_{hashlib.md5(profile_name.encode()).hexdigest()[:6]}",
                        "name": profile_name.strip(),
                        "icon": profile_icon,
                        "description": profile_description.strip() or f"Custom profile for {profile_name}",
                        "avoid": avoid_list,
                        "watch": watch_list,
                        "severity": severity.lower(),
                        "created_at": datetime.now().isoformat()
                    }
                    
                    st.session_state.custom_profiles.append(new_profile)
                    st.session_state.selected_custom_profiles.append(new_profile['id'])  # Auto-activate
                    st.success(f"✓ Profile '{profile_name}' created and activated!")
                    st.balloons()
                    st.rerun()
    
    with tab_manage:
        if st.session_state.custom_profiles:
            # Filter/sort options
            st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns([2, 1])
            with col2:
                show_active_only = st.checkbox("Show active only", value=False)
            
            profiles_to_show = st.session_state.custom_profiles
            if show_active_only:
                profiles_to_show = [p for p in profiles_to_show if p['id'] in st.session_state.selected_custom_profiles]
            
            for i, profile in enumerate(profiles_to_show):
                is_active = profile['id'] in st.session_state.selected_custom_profiles
                severity = profile.get("severity", "medium")
                icon = profile.get("icon", "🏷️")
                
                severity_config = {
                    "low": {"color": "var(--success)", "bg": "var(--success-soft)", "label": "Low Risk"},
                    "medium": {"color": "var(--warning)", "bg": "var(--warning-soft)", "label": "Medium Risk"},
                    "high": {"color": "var(--danger)", "bg": "var(--danger-soft)", "label": "High Risk"}
                }.get(severity, {"color": "var(--warning)", "bg": "var(--warning-soft)", "label": "Medium Risk"})
                
                active_style = "border-color: var(--accent-primary); background: linear-gradient(135deg, rgba(168, 85, 247, 0.08), rgba(99, 102, 241, 0.05));" if is_active else ""
                
                st.markdown(f"""
                <div class="profile-card {'active' if is_active else ''}" style="{active_style}">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem;">
                                <span style="font-size: 1.75rem;">{icon}</span>
                                <div>
                                    <h3 style="color: var(--text-primary); font-size: 1.15rem; margin: 0; font-weight: 600;">{profile['name']}</h3>
                                    <p style="color: var(--text-muted); font-size: 0.8rem; margin: 0;">{profile.get('description', '')[:60]}{'...' if len(profile.get('description', '')) > 60 else ''}</p>
                                </div>
                            </div>
                            
                            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.75rem;">
                                <span class="severity-badge {severity}">{severity_config['label']}</span>
                                <span style="font-size: 0.75rem; color: var(--text-muted); padding: 0.25rem 0.5rem; background: var(--bg-card); border-radius: 8px;">
                                    🚫 {len(profile.get('avoid', []))} avoid
                                </span>
                                <span style="font-size: 0.75rem; color: var(--text-muted); padding: 0.25rem 0.5rem; background: var(--bg-card); border-radius: 8px;">
                                    ⚠️ {len(profile.get('watch', []))} watch
                                </span>
                            </div>
                            
                            <div style="display: flex; flex-wrap: wrap; gap: 0.25rem;">
                """, unsafe_allow_html=True)
                
                # Show ingredient tags
                tags_html = ""
                for ing in profile.get('avoid', [])[:4]:
                    tags_html += f'<span class="ingredient-tag avoid" style="font-size: 0.7rem; padding: 0.2rem 0.5rem;">🚫 {ing}</span>'
                for ing in profile.get('watch', [])[:3]:
                    tags_html += f'<span class="ingredient-tag watch" style="font-size: 0.7rem; padding: 0.2rem 0.5rem;">⚠️ {ing}</span>'
                remaining = len(profile.get('avoid', [])) + len(profile.get('watch', [])) - 7
                if remaining > 0:
                    tags_html += f'<span class="ingredient-tag" style="font-size: 0.7rem; padding: 0.2rem 0.5rem;">+{remaining} more</span>'
                
                st.markdown(f"""
                            {tags_html}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Action buttons
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col2:
                    if st.button(
                        "✓ Active" if is_active else "Activate",
                        key=f"toggle_{profile['id']}_{i}",
                        type="primary" if is_active else "secondary",
                        use_container_width=True
                    ):
                        if is_active:
                            st.session_state.selected_custom_profiles.remove(profile['id'])
                        else:
                            st.session_state.selected_custom_profiles.append(profile['id'])
                        st.rerun()
                with col3:
                    if st.button("📝", key=f"edit_{profile['id']}_{i}", use_container_width=True, help="Edit profile"):
                        st.session_state[f"editing_{profile['id']}"] = True
                        st.rerun()
                with col4:
                    if st.button("🗑️", key=f"delete_{profile['id']}_{i}", use_container_width=True, help="Delete profile"):
                        st.session_state.custom_profiles = [p for p in st.session_state.custom_profiles if p['id'] != profile['id']]
                        if profile['id'] in st.session_state.selected_custom_profiles:
                            st.session_state.selected_custom_profiles.remove(profile['id'])
                        st.rerun()
                
                st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
            
            # Summary
            if active_count > 0:
                st.markdown(f"""
                <div style="margin-top: 1rem; padding: 1rem 1.25rem; background: linear-gradient(135deg, rgba(168, 85, 247, 0.1), rgba(99, 102, 241, 0.08)); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 16px;">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <span style="font-size: 1.5rem;">✨</span>
                        <div>
                            <p style="margin: 0; color: var(--accent-primary); font-weight: 600; font-size: 0.95rem;">
                                {active_count} profile(s) active
                            </p>
                            <p style="margin: 0; color: var(--text-muted); font-size: 0.8rem;">
                                These profiles will be used when analyzing ingredients
                            </p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            # Empty state
            st.markdown("""
            <div class="empty-state glass-card">
                <div class="empty-state-icon">🏷️</div>
                <h3 style="color: var(--text-primary); margin: 0 0 0.5rem 0;">No Custom Profiles Yet</h3>
                <p style="color: var(--text-muted); margin: 0; max-width: 300px; margin: 0 auto;">
                    Create your first custom profile to personalize ingredient analysis for your specific health needs.
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab_templates:
        st.markdown("""
        <div class="glass-card" style="margin-top: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
                <span style="font-size: 1.5rem;">⚡</span>
                <div>
                    <h3 style="color: var(--text-primary); margin: 0; font-size: 1.1rem;">Quick Start Templates</h3>
                    <p style="color: var(--text-muted); margin: 0; font-size: 0.85rem;">One-click profiles for common needs</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Template cards
        templates = [
            {
                "name": "Migraine Prevention",
                "icon": "🧠",
                "description": "Avoid common migraine trigger foods",
                "avoid": ["tyramine", "msg", "nitrates", "nitrites", "aged cheese", "red wine", "chocolate", "aspartame", "sulfites"],
                "watch": ["caffeine", "alcohol", "citrus", "gluten"],
                "severity": "high"
            },
            {
                "name": "Low Histamine",
                "icon": "🌿",
                "description": "For histamine intolerance management",
                "avoid": ["fermented foods", "aged cheese", "wine", "beer", "vinegar", "sauerkraut", "soy sauce", "fish sauce"],
                "watch": ["tomatoes", "spinach", "avocado", "eggplant", "citrus"],
                "severity": "high"
            },
            {
                "name": "Anti-Inflammatory",
                "icon": "❤️",
                "description": "Reduce inflammatory ingredients",
                "avoid": ["trans fat", "hydrogenated oil", "high fructose corn syrup", "msg", "artificial sweeteners"],
                "watch": ["sugar", "refined flour", "vegetable oil", "corn oil", "soybean oil"],
                "severity": "medium"
            },
            {
                "name": "Clean Eating",
                "icon": "🍎",
                "description": "Avoid artificial additives and preservatives",
                "avoid": ["artificial colors", "artificial flavors", "bht", "bha", "tbhq", "sodium benzoate", "potassium sorbate"],
                "watch": ["natural flavors", "citric acid", "maltodextrin", "dextrose"],
                "severity": "low"
            }
        ]
        
        cols = st.columns(2)
        for i, template in enumerate(templates):
            with cols[i % 2]:
                sev_colors = {"low": "var(--success)", "medium": "var(--warning)", "high": "var(--danger)"}
                st.markdown(f"""
                <div class="interactive-card glass-card" style="margin-bottom: 0.5rem;">
                    <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
                        <span style="font-size: 2rem;">{template['icon']}</span>
                        <div style="flex: 1;">
                            <h4 style="color: var(--text-primary); margin: 0; font-size: 1rem;">{template['name']}</h4>
                            <p style="color: var(--text-muted); font-size: 0.8rem; margin: 0.25rem 0;">{template['description']}</p>
                            <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                                <span style="font-size: 0.7rem; color: {sev_colors[template['severity']]}; background: {sev_colors[template['severity']]}15; padding: 0.15rem 0.4rem; border-radius: 6px;">
                                    {template['severity'].upper()}
                                </span>
                                <span style="font-size: 0.7rem; color: var(--text-muted);">
                                    {len(template['avoid'])} avoid · {len(template['watch'])} watch
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Add {template['name']}", key=f"template_{i}", use_container_width=True):
                    new_profile = {
                        "id": f"custom_template_{hashlib.md5(template['name'].encode()).hexdigest()[:6]}",
                        "name": template['name'],
                        "icon": template['icon'],
                        "description": template['description'],
                        "avoid": template['avoid'],
                        "watch": template['watch'],
                        "severity": template['severity'],
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # Check if already exists
                    existing_names = [p['name'] for p in st.session_state.custom_profiles]
                    if template['name'] not in existing_names:
                        st.session_state.custom_profiles.append(new_profile)
                        st.session_state.selected_custom_profiles.append(new_profile['id'])
                        st.success(f"✓ {template['name']} added and activated!")
                        st.rerun()
                    else:
                        st.warning(f"Profile '{template['name']}' already exists")
    
    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
    
    if st.button("← Back to Scanner", use_container_width=True):
        st.session_state.current_view = "main"
        st.rerun()


def render_sidebar():
    """Render sidebar navigation."""
    with st.sidebar:
        st.markdown("""
        <div style="padding: 1rem 0;">
            <h2 style="color: var(--text-primary); font-size: 1.5rem; margin: 0;">LabelLens</h2>
            <p style="color: var(--text-muted); font-size: 0.85rem; margin: 0.25rem 0 0 0;">Menu</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<hr style='border-color: var(--border-subtle); margin: 1rem 0;'>", unsafe_allow_html=True)
        
        if st.button("🔍 Scanner", use_container_width=True, type="primary" if st.session_state.current_view == "main" else "secondary"):
            st.session_state.current_view = "main"
            st.session_state.analysis_result = None
            st.rerun()
        
        if st.button(f"📋 History ({len(st.session_state.scan_history)})", use_container_width=True, type="primary" if st.session_state.current_view == "history" else "secondary"):
            st.session_state.current_view = "history"
            st.rerun()
        
        custom_count = len(st.session_state.custom_profiles)
        active_custom = len(st.session_state.selected_custom_profiles)
        custom_label = f"🏷️ Custom Profiles ({active_custom}/{custom_count})" if custom_count else "🏷️ Custom Profiles"
        if st.button(custom_label, use_container_width=True, type="primary" if st.session_state.current_view == "custom_profiles" else "secondary"):
            st.session_state.current_view = "custom_profiles"
            st.rerun()
        
        if st.button("📊 Insights", use_container_width=True, type="primary" if st.session_state.current_view == "stats" else "secondary"):
            st.session_state.current_view = "stats"
            st.rerun()
        
        st.markdown("<hr style='border-color: var(--border-subtle); margin: 1rem 0;'>", unsafe_allow_html=True)
        
        # Quick stats in sidebar
        if st.session_state.scan_history:
            total = len(st.session_state.scan_history)
            safe = sum(1 for h in st.session_state.scan_history if h['verdict'] == 'SAFE')
            st.markdown(f"""
            <div style="padding: 0.75rem; background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border-subtle);">
                <p style="color: var(--text-muted); font-size: 0.75rem; margin: 0;">Quick Stats</p>
                <p style="color: var(--text-primary); font-size: 0.9rem; margin: 0.5rem 0 0 0;">
                    {safe}/{total} products safe
                </p>
            </div>
            """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    
    # Initialize
    init_session_state()
    
    # Render premium animated background
    render_animated_background()
    
    # API key check
    if not GROQ_API_KEY:
        st.markdown("""
        <div class="glass-card" style="text-align: center; margin-top: 3rem;">
            <p style="font-size: 2rem; margin: 0;">🔑</p>
            <p style="color: var(--text-primary); font-weight: 600; margin: 1rem 0 0.5rem 0;">API Key Required</p>
            <p style="color: var(--text-secondary); margin: 0;">Add your Groq API key to the .env file</p>
            <code style="display: block; margin-top: 1rem; padding: 0.75rem; background: var(--bg-secondary); border-radius: 8px; color: var(--accent-primary);">GROQ_API_KEY=your_key_here</code>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    
    # Show onboarding for first-time users
    if st.session_state.show_onboarding:
        render_onboarding()
        return
    
    # Render sidebar
    render_sidebar()
    
    # Route to appropriate view
    if st.session_state.current_view == "history":
        render_history()
    elif st.session_state.current_view == "stats":
        render_statistics()
    elif st.session_state.current_view == "custom_profiles":
        render_custom_profiles()
    else:
        # Main scanner view
        render_header()
        
        # If we have results, show them
        if st.session_state.analysis_result:
            render_results(st.session_state.analysis_result)
        else:
            # Profile selector
            user_profile = render_profile_selector()
            
            # Input tabs
            tab_scan, tab_type = st.tabs(["Scan Label", "Type Ingredients"])
            
            with tab_scan:
                render_scan_section()
            
            with tab_type:
                pass  # Text input is shown below
            
            # Text input (always visible)
            ingredients = render_text_input()
            
            # Analyze button
            render_analyze_button(user_profile, ingredients)
    
    # Footer with premium styling
    st.markdown("""
    <div style="text-align: center; padding: 3.5rem 0 2.5rem 0; margin-top: 3rem; border-top: 1px solid rgba(139, 92, 246, 0.2); position: relative; overflow: hidden;">
        <div style="position: absolute; top: 0; left: 50%; transform: translateX(-50%); width: 200px; height: 1px; background: linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.5), rgba(6, 182, 212, 0.5), transparent);"></div>
        <div style="display: flex; align-items: center; justify-content: center; gap: 0.75rem; margin-bottom: 1rem;">
            <div style="width: 36px; height: 36px; background: linear-gradient(135deg, #8b5cf6, #06b6d4); border-radius: 10px; display: flex; align-items: center; justify-content: center; box-shadow: 0 6px 20px rgba(139, 92, 246, 0.3);">
                <span style="font-size: 1.1rem;">🔍</span>
            </div>
            <span style="font-size: 1.2rem; font-weight: 700; background: linear-gradient(135deg, #fff, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">LabelLens</span>
        </div>
        <p style="color: rgba(255,255,255,0.5); font-size: 0.85rem; margin: 0;">
            Powered by <span style="color: #8b5cf6; font-weight: 600;">Groq AI</span> • Built with ❤️ for Hackathon 2026
        </p>
        <div style="display: flex; align-items: center; justify-content: center; gap: 1.5rem; margin-top: 1.25rem;">
            <a href="https://github.com" target="_blank" style="color: rgba(255,255,255,0.6); font-size: 0.9rem; text-decoration: none; transition: all 0.3s ease;">GitHub</a>
            <span style="color: rgba(255,255,255,0.3);">•</span>
            <span style="color: rgba(255,255,255,0.5); font-size: 0.85rem;">For informational purposes only</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
