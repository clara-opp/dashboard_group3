# ============================================================
# pathfind_design.py - v18 FINAL - NO DOPPELTE KÄSTEN
# ============================================================

import streamlit as st
import base64
import os
from pathlib import Path

def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

def find_background_image(img_file="background.jpg"):
    possible_dirs = [
        "personas",
        "./personas",
        os.path.join(os.getcwd(), "personas"),
        os.path.join(os.path.dirname(__file__), "..", "personas"),
        str(Path(__file__).parent.parent / "personas"),
    ]
    for img_dir in possible_dirs:
        try:
            img_path = os.path.join(img_dir, img_file)
            if os.path.exists(img_path) and os.path.isfile(img_path):
                b64_img = get_img_as_base64(img_path)
                if b64_img:
                    return b64_img
        except Exception:
            pass
    return ""

def setup_complete_design():
    st.markdown("""
    <style>
        :root {
            color-scheme: dark !important;
            zoom: 80% !important;
        }
        html, body {
            color-scheme: dark !important;
            zoom: 80% !important;
            transform-origin: top left;
            width: 200%;
            height: 200%;
        }
    </style>
    """, unsafe_allow_html=True)
    
    bin_str = find_background_image("background.jpg")
    if not bin_str:
        st.warning("⚠️ Background image not found")

    complete_css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Audiowide&family=Space+Mono:wght@700&family=Poppins:wght@400;500;600;700;800&display=swap');
    
    :root {{
        color-scheme: dark !important;
        zoom: 80% !important;
    }}
    
    html, body {{
        color-scheme: dark !important;
        zoom: 80% !important;
        transform-origin: top left;
        width: 200%;
        height: 200%;
    }}
    
    html, body, [data-testid="stAppViewContainer"], .stApp {{
        background-image: url("data:image/jpeg;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
        margin: 0;
        padding: 0;
        background-color: #0a0f1e !important;
    }}
    
    * {{
        color: rgba(255, 255, 255, 1) !important;
    }}
    
    body, .stMarkdown, span, label, p, div {{
        color: rgba(255, 255, 255, 1) !important;
        font-family: 'Poppins', sans-serif !important;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6) !important;
    }}
    
    label, h1, h2, h3, h4, h5, h6 {{
        color: rgba(255, 255, 255, 1) !important;
        font-weight: 600 !important;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.8) !important;
    }}
    
    a {{
        color: rgba(100, 200, 255, 1) !important;
        font-weight: 600 !important;
    }}
    
    a:hover {{
        color: rgba(150, 220, 255, 1) !important;
    }}
    
    div[data-testid="stAlert"] {{
        background: rgba(20, 25, 40, 0.9) !important;
        border: 1.5px solid rgba(100, 140, 200, 0.5) !important;
        color: rgba(255, 255, 255, 1) !important;
    }}
    
    div[data-testid="stMetric"] {{
        background: rgba(20, 25, 40, 0.8) !important;
    }}
    
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] span {{
        color: rgba(255, 255, 255, 1) !important;
        text-shadow: 0 2px 6px rgba(0, 0, 0, 0.5) !important;
    }}
    
    .pathfind-header {{
        text-align: center;
        margin: 1.5rem 0 2rem 0;
        animation: slide-down 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
    }}
    
    .pathfind-logo {{
        font-family: 'Audiowide', sans-serif;
        font-size: 4.2rem;
        font-weight: 900;
        letter-spacing: 5px;
        margin: 0;
        padding: 0;
        color: #FFFFFF;
        text-shadow: 
            0 0 30px rgba(255, 215, 0, 0.9),
            0 0 60px rgba(255, 215, 0, 0.5),
            -3px 3px 0 rgba(0, 0, 0, 0.6);
        filter: drop-shadow(0 0 15px rgba(255, 215, 0, 0.7));
        animation: logo-glow 2.5s ease-in-out infinite;
        display: inline-block;
        padding: 1.2rem 2.5rem;
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.1) 0%, rgba(255, 255, 0, 0.05) 100%);
        border: 2px solid rgba(255, 215, 0, 0.4);
        border-radius: 18px;
        backdrop-filter: blur(10px);
    }}
    
    @keyframes slide-down {{
        from {{
            opacity: 0;
            transform: translateY(-30px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    @keyframes logo-glow {{
        0%, 100% {{
            filter: drop-shadow(0 0 15px rgba(255, 215, 0, 0.7)) brightness(1);
            text-shadow: 
                0 0 30px rgba(255, 215, 0, 0.9),
                0 0 60px rgba(255, 215, 0, 0.5),
                -3px 3px 0 rgba(0, 0, 0, 0.6);
        }}
        50% {{
            filter: drop-shadow(0 0 25px rgba(255, 215, 0, 0.9)) brightness(1.05);
            text-shadow: 
                0 0 40px rgba(255, 215, 0, 1),
                0 0 80px rgba(255, 215, 0, 0.7),
                -3px 3px 0 rgba(0, 0, 0, 0.6);
        }}
    }}
    
    .pathfind-icon {{
        font-size: 3.2rem;
        display: inline-block;
        margin-right: 0.8rem;
        animation: float-plane 3s ease-in-out infinite;
        filter: drop-shadow(0 0 12px rgba(255, 215, 0, 0.6));
    }}
    
    @keyframes float-plane {{
        0%, 100% {{
            transform: translateY(0px) rotate(0deg);
        }}
        25% {{
            transform: translateY(-12px) rotate(-5deg);
        }}
        50% {{
            transform: translateY(0px) rotate(0deg);
        }}
        75% {{
            transform: translateY(-12px) rotate(5deg);
        }}
    }}
    
    .pathfind-subtitle {{
        font-family: 'Space Mono', monospace;
        font-size: 0.9rem;
        letter-spacing: 3px;
        color: rgba(255, 255, 255, 0.9);
        text-transform: uppercase;
        margin-top: 0.6rem;
        padding: 0.8rem 0;
        border-top: 1px solid rgba(255, 215, 0, 0.25);
        border-bottom: 1px solid rgba(255, 215, 0, 0.25);
        font-weight: 600;
        animation: fade-in 1s ease-out 0.4s backwards;
        text-shadow: 0 2px 6px rgba(0, 0, 0, 0.5) !important;
    }}
    
    @keyframes fade-in {{
        from {{
            opacity: 0;
            transform: translateY(10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    button, .stButton button, .stButton > button, input[type="button"], input[type="submit"], [data-testid="stButton"] button {{
        background: rgba(25, 35, 55, 0.95) !important;
        border: 1.5px solid rgba(80, 120, 180, 0.7) !important;
        color: rgba(255, 255, 255, 0.99) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.7rem 1.5rem !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
    }}
    
    button:hover, .stButton button:hover, [data-testid="stButton"] button:hover {{
        background: rgba(50, 70, 100, 0.98) !important;
        border: 1.5px solid rgba(100, 150, 220, 0.9) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
        transform: translateY(-2px) !important;
    }}
    
    input, .stTextInput > div > div > input, .stDateInput > div > div > input, .stNumberInput > div > div > input, textarea {{
        background: rgba(10, 15, 35, 0.8) !important;
        border: 1.5px solid rgba(80, 120, 180, 0.5) !important;
        color: rgba(255, 255, 255, 1) !important;
        border-radius: 10px !important;
        padding: 0.85rem 1.1rem !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
    }}
    
    input::placeholder {{
        color: rgba(255, 255, 255, 0.4) !important;
    }}
    
    input:focus, .stTextInput > div > div > input:focus, textarea:focus {{
        border: 1.5px solid rgba(100, 180, 255, 1) !important;
        box-shadow: 0 0 30px rgba(100, 180, 255, 0.5) !important;
        background: rgba(10, 15, 35, 0.95) !important;
    }}
    
    input[type="radio"], input[type="checkbox"] {{
        accent-color: #64C8FF !important;
    }}
    
    input[type="radio"]:checked, input[type="checkbox"]:checked {{
        accent-color: #00FFFF !important;
    }}
    
    [role="progressbar"] {{
        background: rgba(80, 120, 180, 0.2) !important;
    }}
    
    [role="progressbar"] > div {{
        background: linear-gradient(90deg, #64C8FF 0%, #7ED4FF 50%, #64C8FF 100%) !important;
        box-shadow: 0 0 20px rgba(100, 200, 255, 0.6) !important;
    }}
    
    [data-testid="stTabs"] button {{
        background: transparent !important;
        color: rgba(255, 255, 255, 0.85) !important;
        font-weight: 600 !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
    }}
    
    [data-testid="stTabs"] button[aria-selected="true"] {{
        color: rgba(100, 200, 255, 1) !important;
        border-bottom: 3px solid rgba(100, 200, 255, 0.95) !important;
    }}
    
    ::-webkit-scrollbar {{
        width: 10px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: rgba(255, 255, 255, 0.05);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: rgba(100, 200, 255, 0.55);
        border-radius: 5px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(100, 200, 255, 0.85);
    }}
    
    hr {{
        border-color: rgba(255, 255, 255, 0.15) !important;
    }}
    
    @media (max-width: 768px) {{
        .pathfind-logo {{
            font-size: 3rem;
            padding: 1rem 2rem;
        }}
        .pathfind-icon {{
            font-size: 2.5rem;
            margin-right: 0.5rem;
        }}
        .pathfind-subtitle {{
            font-size: 0.8rem;
            letter-spacing: 2px;
        }}
    }}
    
    @media (max-width: 480px) {{
        .pathfind-logo {{
            font-size: 2.2rem;
            padding: 0.8rem 1.5rem;
            letter-spacing: 2px;
        }}
        .pathfind-icon {{
            font-size: 2rem;
            margin-right: 0.3rem;
        }}
        .pathfind-subtitle {{
            font-size: 0.7rem;
            letter-spacing: 1px;
        }}
    }}
    </style>
    """
    
    st.markdown(complete_css, unsafe_allow_html=True)

def render_pathfind_header():
    st.markdown('''
        <div class="pathfind-header">
            <div class="pathfind-logo">
                <span class="pathfind-icon">✈️</span>
                PATHFIND
            </div>
            <div class="pathfind-subtitle">Your Next Adventure Awaits</div>
        </div>
    ''', unsafe_allow_html=True)
