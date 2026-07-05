import re
import datetime
import streamlit as st

def validate_input(text: str) -> tuple[bool, str]:
    """
    STRIDE Security Gate: Tampering (T) & Denial of Service (D)
    Caps input length to 1500 characters and rejects common prompt injection terms.
    """
    if len(text) > 1500:
        return False, "Input length exceeds the safety cap of 1500 characters. Please shorten your description."
    
    # Common prompt injection patterns (case insensitive)
    injection_patterns = [
        r"ignore\s+previous\s+instructions",
        r"system\s+prompt",
        r"you\s+are\s+now\s+a",
        r"ignore\s+above\s+instructions",
        r"bypass\s+restrictions",
        r"override\s+system",
        r"reveal\s+instruction",
        r"developer\s+mode",
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            log_transaction("Safety Check Failed (Prompt Injection Blocked)")
            return False, "Safety Alert: Input contains potential unauthorized commands or instructions. Please describe symptoms only."
            
    return True, ""

def log_transaction(message: str):
    """
    STRIDE Security Gate: Repudiation (R)
    Prints transaction boundaries with timestamps to the backend terminal console.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def inject_custom_css():
    """
    Injects high-fidelity Neumorphic and 3D styled CSS.
    Uses traditional color palettes (Saffron/Gold, Ayurvedic Emerald, Soft Amber).
    """
    st.markdown("""
        <style>
        /* Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,400&display=swap');
        
        /* Global CSS Overrides */
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif;
        }
        
        h1, h2, h3 {
            font-family: 'Playfair Display', serif;
            font-weight: 700;
            color: #2E5A44; /* Ayurvedic Dark Forest Green */
        }
        
        /* Neumorphic Containers */
        .neumorphic-card {
            background: #f8faff;
            border-radius: 20px;
            padding: 24px;
            box-shadow: 8px 8px 16px #d1d9e6, -8px -8px 16px #ffffff;
            margin-bottom: 24px;
            border: 1px solid rgba(255, 255, 255, 0.7);
            transition: all 0.3s ease;
        }
        
        .neumorphic-card:hover {
            transform: translateY(-4px);
            box-shadow: 12px 12px 20px #c2cbd9, -12px -12px 20px #ffffff;
        }
        
        /* 3D Gold Accent Tag */
        .badge-saffron {
            background: linear-gradient(135deg, #FF9933 0%, #FFB366 100%);
            color: white;
            padding: 6px 14px;
            border-radius: 50px;
            font-weight: 600;
            font-size: 0.85rem;
            display: inline-block;
            box-shadow: 0 4px 10px rgba(255, 153, 51, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
        }
        
        .badge-gold {
            background: linear-gradient(135deg, #D4AF37 0%, #F3E5AB 100%);
            color: #3d3000;
            padding: 6px 14px;
            border-radius: 50px;
            font-weight: 600;
            font-size: 0.85rem;
            display: inline-block;
            box-shadow: 0 4px 10px rgba(212, 175, 55, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .badge-emerald {
            background: linear-gradient(135deg, #2E5A44 0%, #468466 100%);
            color: white;
            padding: 6px 14px;
            border-radius: 50px;
            font-weight: 600;
            font-size: 0.85rem;
            display: inline-block;
            box-shadow: 0 4px 10px rgba(46, 90, 68, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.2);
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
        }
        
        /* Modern 3D illustrative styling for buttons */
        div.stButton > button {
            background: linear-gradient(135deg, #2E5A44 0%, #1e3c2d 100%) !important;
            color: white !important;
            font-weight: 600 !important;
            border-radius: 12px !important;
            padding: 12px 28px !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(46, 90, 68, 0.4) !important;
            transition: all 0.3s ease !important;
        }
        
        div.stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(46, 90, 68, 0.6) !important;
            background: linear-gradient(135deg, #376d52 0%, #254a37 100%) !important;
        }
        
        div.stButton > button:active {
            transform: translateY(1px) !important;
            box-shadow: 0 2px 10px rgba(46, 90, 68, 0.4) !important;
        }
        
        /* Custom card elements for articles */
        .article-card {
            background: #ffffff;
            border-left: 5px solid #FF9933; /* Saffron Border Accent */
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            transition: all 0.2s ease;
        }
        .article-card:hover {
            box-shadow: 0 8px 24px rgba(0,0,0,0.1);
            transform: scale(1.01);
        }
        .article-meta {
            font-size: 0.85rem;
            color: #666;
            margin-bottom: 10px;
        }
        .article-title {
            color: #2E5A44;
            margin-bottom: 8px;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)
