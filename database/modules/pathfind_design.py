# ============================================================
# pathfind_design_v2.py - CLOUD SAFE + BLUR BOXES
# ============================================================
# Production stable for Cloud Foundry + Local
# No browser storage, responsive, blur containers
# ============================================================

import streamlit as st
import base64
import os
from pathlib import Path


def get_img_as_base64(file_path: str) -> str:
    """Convert image file to base64."""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""


def find_background_image(img_file: str = "background.jpg") -> str:
    """Find background image in multiple possible directories."""
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


def setup_complete_design() -> None:
    """Setup dark design with blur boxes as main content containers."""
    
    bin_str = find_background_image("background.jpg")
    if not bin_str:
        st.warning("⚠️ Background image not found")

    complete_css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Audiowide&family=Space+Mono:wght@700&family=Poppins:wght@400;500;600;700;800&display=swap');

    /* ========================================
       ROOT & DARK MODE
       ======================================== */
    :root {{
        color-scheme: dark !important;
    }}

    html, body {{
        color-scheme: dark !important;
        background-color: #0a0f1e !important;
        margin: 0;
        padding: 0;
    }}

    /* App container background - FIXED NO SCROLL */
    [data-testid="stAppViewContainer"] {{
        background-color: #0a0f1e !important;
        background-image: url("data:image/jpeg;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    /* Container width */
    .block-container {{
        max-width: 90% !important;
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }}

    /* ========================================
       TEXT - DARK MODE
       ======================================== */
    body, .stMarkdown, span, label, p, div {{
        color: rgba(255, 255, 255, 0.95) !important;
        font-family: 'Poppins', sans-serif !important;
    }}

    h1, h2, h3, h4, h5, h6 {{
        color: rgba(255, 255, 255, 1) !important;
        font-weight: 600 !important;
    }}

    a {{
        color: rgba(100, 200, 255, 1) !important;
        font-weight: 600 !important;
    }}

    a:hover {{
        color: rgba(150, 220, 255, 1) !important;
    }}

    /* ========================================
       BLUR CONTAINERS - PRIMARY DESIGN
       ======================================== */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background: rgba(15, 20, 40, 0.50) !important;
        backdrop-filter: blur(25px) !important;
        -webkit-backdrop-filter: blur(25px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        box-shadow: 
            0 4px 16px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
        color: rgba(255, 255, 255, 1) !important;
        padding: 1.5rem !important;
        margin: 1.2rem 0 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    [data-testid="stVerticalBlockBorderWrapper"]:hover {{
        background: rgba(15, 20, 40, 0.65) !important;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
    }}

    /* ========================================
       ALERTS WITH BLUR
       ======================================== */
    div[data-testid="stAlert"] {{
        background: rgba(20, 25, 40, 0.75) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(100, 140, 200, 0.6) !important;
        border-radius: 12px !important;
        color: rgba(255, 255, 255, 1) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
    }}

    /* ========================================
       BUTTONS WITH BLUR
       ======================================== */
    button,
    .stButton button,
    [data-testid="stButton"] button {{
        background: rgba(25, 35, 55, 0.80) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(80, 120, 180, 0.7) !important;
        color: rgba(255, 255, 255, 0.99) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.7rem 1.6rem !important;
        transition: all 0.25s ease !important;
        cursor: pointer !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
    }}

    button:hover,
    .stButton button:hover,
    [data-testid="stButton"] button:hover {{
        background: rgba(50, 70, 100, 0.90) !important;
        border: 1px solid rgba(100, 150, 220, 0.9) !important;
        box-shadow: 0 4px 16px rgba(100, 150, 220, 0.3) !important;
        transform: translateY(-2px) !important;
    }}

    button:active,
    .stButton button:active {{
        transform: translateY(0) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
    }}

    /* ========================================
       INPUTS WITH BLUR
       ======================================== */
    input,
    .stTextInput > div > div > input,
    .stDateInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select,
    textarea {{
        background: rgba(10, 15, 35, 0.75) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(80, 120, 180, 0.5) !important;
        color: rgba(255, 255, 255, 1) !important;
        border-radius: 10px !important;
        padding: 0.7rem 1rem !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.15) !important;
    }}

    input:focus,
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    textarea:focus {{
        border: 1px solid rgba(100, 180, 255, 1) !important;
        box-shadow: 
            inset 0 2px 4px rgba(0, 0, 0, 0.15),
            0 0 20px rgba(100, 180, 255, 0.5) !important;
        background: rgba(10, 15, 35, 0.85) !important;
    }}

    input::placeholder {{
        color: rgba(255, 255, 255, 0.35) !important;
    }}

    /* ========================================
       LOGO HEADER
       ======================================== */
    .pathfind-header {{
        text-align: center;
        margin: 1.5rem 0 2rem 0;
        padding: 1.5rem;
        background: rgba(15, 20, 40, 0.40) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 215, 0, 0.25) !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
    }}

    .pathfind-logo {{
        font-family: 'Audiowide', sans-serif;
        font-size: clamp(2rem, 5vw, 3.2rem);
        font-weight: 900;
        letter-spacing: 3px;
        color: #FFFFFF;
        text-shadow: 0 0 25px rgba(255, 215, 0, 0.9);
        display: inline-block;
        padding: 0.8rem 2rem;
        background: linear-gradient(135deg, rgba(255,215,0,0.12) 0%, rgba(255,255,0,0.05) 100%);
        border: 1px solid rgba(255, 215, 0, 0.4);
        border-radius: 14px;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }}

    .pathfind-icon {{
        font-size: clamp(1.8rem, 4vw, 2.5rem);
        display: inline-block;
        margin-right: 0.6rem;
        filter: drop-shadow(0 0 12px rgba(255, 215, 0, 0.6));
        animation: float 3s ease-in-out infinite;
    }}

    @keyframes float {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-8px); }}
    }}

    .pathfind-subtitle {{
        font-family: 'Space Mono', monospace;
        font-size: clamp(0.7rem, 1.2vw, 0.85rem);
        letter-spacing: 2.5px;
        color: rgba(255, 255, 255, 0.9);
        text-transform: uppercase;
        margin-top: 0.8rem;
        padding: 0.8rem 0;
        border-top: 1px solid rgba(255, 215, 0, 0.25);
        border-bottom: 1px solid rgba(255, 215, 0, 0.25);
        font-weight: 600;
    }}

    /* ========================================
       RADIO / CHECKBOX
       ======================================== */
    input[type="radio"],
    input[type="checkbox"] {{
        accent-color: #64C8FF !important;
    }}

    input[type="radio"]:checked,
    input[type="checkbox"]:checked {{
        accent-color: #00FFFF !important;
    }}

    /* ========================================
       PROGRESS BAR
       ======================================== */
    [role="progressbar"] {{
        background: rgba(80, 120, 180, 0.2) !important;
        border-radius: 8px !important;
    }}

    [role="progressbar"] > div {{
        background: linear-gradient(90deg, #64C8FF 0%, #7ED4FF 100%) !important;
        border-radius: 8px !important;
        box-shadow: 0 0 15px rgba(100, 200, 255, 0.4) !important;
    }}

    /* ========================================
       TABS WITH BLUR
       ======================================== */
    [data-testid="stTabs"] {{
        background: rgba(20, 25, 40, 0.5) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border-radius: 12px !important;
        padding: 0.5rem !important;
    }}

    [data-testid="stTabs"] button {{
        background: transparent !important;
        color: rgba(255, 255, 255, 0.75) !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }}

    [data-testid="stTabs"] button[aria-selected="true"] {{
        background: rgba(100, 200, 255, 0.15) !important;
        color: rgba(100, 200, 255, 1) !important;
        border-bottom: 2px solid rgba(100, 200, 255, 1) !important;
        box-shadow: 0 2px 8px rgba(100, 200, 255, 0.2) !important;
    }}

    /* ========================================
       SCROLLBAR
       ======================================== */
    ::-webkit-scrollbar {{
        width: 10px;
    }}

    ::-webkit-scrollbar-track {{
        background: rgba(255, 255, 255, 0.05);
        border-radius: 5px;
    }}

    ::-webkit-scrollbar-thumb {{
        background: rgba(100, 200, 255, 0.5);
        border-radius: 5px;
        backdrop-filter: blur(5px);
    }}

    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(100, 200, 255, 0.8);
    }}

    /* ========================================
       HR & DIVIDERS
       ======================================== */
    hr {{
        border-color: rgba(255, 255, 255, 0.12) !important;
        border-style: solid !important;
    }}

    /* ========================================
       METRIC BOXES
       ======================================== */
    [data-testid="stMetric"] {{
        background: rgba(20, 25, 40, 0.65) !important;
        backdrop-filter: blur(18px) !important;
        -webkit-backdrop-filter: blur(18px) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 1.5rem !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
    }}

    [data-testid="stMetric"]:hover {{
        background: rgba(20, 25, 40, 0.75) !important;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3) !important;
    }}

    /* ========================================
       EXPANDABLE SECTIONS
       ======================================== */
    details {{
        background: rgba(20, 25, 40, 0.55) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin: 0.8rem 0 !important;
    }}

    details summary {{
        cursor: pointer;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.95);
        transition: color 0.2s ease;
    }}

    details summary:hover {{
        color: rgba(100, 200, 255, 1);
    }}

    /* ========================================
       MOBILE RESPONSIVE
       ======================================== */
    @media (max-width: 768px) {{
        .block-container {{
            max-width: 95% !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }}

        [data-testid="stVerticalBlockBorderWrapper"] {{
            padding: 1.2rem !important;
            margin: 1rem 0 !important;
        }}
    }}

    @media (max-width: 480px) {{
        .block-container {{
            max-width: 100% !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}

        .pathfind-header {{
            padding: 1rem;
            margin: 1rem 0 1.5rem 0;
        }}

        .pathfind-logo {{
            font-size: clamp(1.5rem, 4vw, 2rem);
            padding: 0.6rem 1.4rem;
        }}

        .pathfind-icon {{
            font-size: clamp(1.4rem, 3vw, 1.8rem);
            margin-right: 0.4rem;
        }}

        [data-testid="stVerticalBlockBorderWrapper"] {{
            padding: 1rem !important;
            margin: 0.8rem 0 !important;
            border-radius: 12px !important;
        }}

        button,
        .stButton button {{
            padding: 0.6rem 1.2rem !important;
        }}
    }}
    </style>
    """

    st.markdown(complete_css, unsafe_allow_html=True)


def render_pathfind_header() -> None:
    """Render PATHFIND header with blur container."""
    st.markdown(
        '''
        <div class="pathfind-header">
            <div class="pathfind-logo">
                <span class="pathfind-icon">✈️</span>
                PATHFIND
            </div>
            <div class="pathfind-subtitle">Your Next Adventure Awaits</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

