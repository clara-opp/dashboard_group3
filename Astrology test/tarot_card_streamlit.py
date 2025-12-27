
import streamlit as st
import requests
import time
import json
import random
import os
from dotenv import load_dotenv
load_dotenv()

# WICHTIG: set_page_config muss ganz am Anfang stehen, VOR allen anderen st. Befehlen
st.set_page_config(page_title="Mystical Travel Planner", page_icon="🔮", layout="wide")

# RoxyAPI Configuration
API_KEY = os.getenv("ROXY_API_KEY")
TAROT_URL = "https://roxyapi.com/api/v1/data/astro/tarot"

# Load Tarot Database (NACH set_page_config)
@st.cache_data
def load_tarot_database():
    with open('complete_tarot_travel_database.json', 'r', encoding='utf-8') as f:
        return json.load(f)

tarot_db = load_tarot_database()

# Styling
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #eee;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 20px;
        padding: 20px;
        border-radius: 15px;
        border: none;
        font-weight: bold;
        transition: transform 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.05);
    }
    .destination-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .keyword-badge {
        display: inline-block;
        background: rgba(102, 126, 234, 0.3);
        padding: 5px 15px;
        border-radius: 20px;
        margin: 5px;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function to find card in database
def find_card_in_database(card_name, is_reversed):
    # Search in Major Arcana
    for card in tarot_db['major_arcana']:
        if card['name'].lower() == card_name.lower():
            return card['reversed'] if is_reversed else card['upright'], card['name'], 'major'
    
    # Search in Minor Arcana
    for suit in ['cups', 'wands', 'swords', 'pentacles']:
        for card in tarot_db['minor_arcana'][suit]:
            if card['name'].lower() == card_name.lower():
                return card['reversed'] if is_reversed else card['upright'], card['name'], suit
    
    return None, None, None

# Title
st.markdown("<h1 style='text-align: center; color: #667eea;'>🔮 Mystical Travel Planner</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px;'>Draw a tarot card and discover your perfect travel destination</p>", unsafe_allow_html=True)

st.markdown("---")

# Main draw button
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("🃏 Draw Your Travel Card", key="draw_card"):
        
        # Animation
        with st.spinner(""):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(100):
                progress_bar.progress(i + 1)
                if i < 30:
                    status_text.markdown("### ✨ Shuffling the cards...")
                elif i < 60:
                    status_text.markdown("### 🌟 Activating cosmic forces...")
                elif i < 90:
                    status_text.markdown("### 🔮 Your card is being selected...")
                time.sleep(0.02)
            
            progress_bar.empty()
            status_text.empty()
        
        # API Call to RoxyAPI
        try:
            url = f"{TAROT_URL}/single-card-draw?token={API_KEY}&reversed_probability=0.3"
            response = requests.get(url)
            
            if response.status_code == 200:
                card = response.json()
                
                # Get card details from database
                card_name = card.get('name', '')
                is_reversed = card.get('is_reversed', False)
                
                card_data, matched_name, card_type = find_card_in_database(card_name, is_reversed)
                
                if card_data:
                    st.success("✨ Your mystical travel card has been drawn!")
                    st.markdown("---")
                    
                    # Display card with details
                    col_card, col_info = st.columns([1, 1])
                    
                    with col_card:
                        orientation = "🔄 Reversed" if is_reversed else "⬆️ Upright"
                        st.markdown(f"### 🎴 {matched_name}")
                        st.markdown(f"**Orientation:** {orientation}")
                        
                        # Display card image from API
                        if card.get('image'):
                            st.image(card['image'], use_container_width=True)
                        
                        # Keywords
                        st.markdown("#### 🔑 Keywords")
                        keywords_html = "".join([f'<span class="keyword-badge">{kw}</span>' for kw in card_data['keywords']])
                        st.markdown(keywords_html, unsafe_allow_html=True)
                    
                    with col_info:
                        st.markdown("#### 📖 Travel Meaning")
                        st.info(card_data['travel_meaning'])
                        
                        if 'travel_style' in card_data:
                            st.markdown("#### ✈️ Recommended Travel Style")
                            st.write(card_data['travel_style'])
                    
                    st.markdown("---")
                    
                    # Display country recommendations
                    st.markdown("## 🌍 Your Perfect Travel Destinations")
                    st.markdown(f"*Based on '{matched_name}' ({orientation})*")
                    
                    countries = card_data.get('countries', [])
                    
                    if countries:
                        # Display top 3 countries in cards
                        cols = st.columns(min(3, len(countries)))
                        
                        for idx, country in enumerate(countries[:3]):
                            with cols[idx]:
                                st.markdown(f"""
                                <div class="destination-card">
                                    <h3>🌍 {country['name']}</h3>
                                    <p style="font-size: 12px; opacity: 0.8; margin: 5px 0;">Country Code: {country['code']}</p>
                                    <p style="margin-top: 10px;"><strong>Why this destination?</strong></p>
                                    <p style="font-size: 14px;">{country.get('reason', 'Perfect match for your card energy')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Show remaining countries in expandable section
                        if len(countries) > 3:
                            with st.expander(f"🌏 Show {len(countries) - 3} more destinations"):
                                for country in countries[3:]:
                                    st.markdown(f"""
                                    **{country['name']} ({country['code']})**  
                                    _{country.get('reason', 'Great destination for this card')}_
                                    """)
                        
                        # Country codes for export
                        st.markdown("---")
                        st.markdown("### 📊 Country Codes (for further processing)")
                        country_codes = [c['code'] for c in countries]
                        st.code(json.dumps(country_codes, indent=2))
                        
                        # Additional insights
                        st.markdown("---")
                        st.markdown("### 💡 Travel Insights")
                        
                        insight_col1, insight_col2 = st.columns(2)
                        
                        with insight_col1:
                            st.markdown("**🎯 Card Type**")
                            if card_type == 'major':
                                st.write("Major Arcana - Significant life journey")
                            else:
                                st.write(f"Minor Arcana ({card_type.title()}) - Day-to-day experiences")
                        
                        with insight_col2:
                            st.markdown("**🧭 Orientation**")
                            if is_reversed:
                                st.write("Reversed - Internal reflection needed")
                            else:
                                st.write("Upright - External action encouraged")
                    
                    else:
                        st.warning("No specific country recommendations available for this card.")
                
                else:
                    st.warning(f"Card '{card_name}' not found in database. Using general recommendations.")
                    
                    # Fallback: show some generic countries
                    st.markdown("### 🌍 General Travel Recommendations")
                    generic_countries = [
                        {"name": "Iceland", "code": "IS", "reason": "Mystical landscapes"},
                        {"name": "New Zealand", "code": "NZ", "reason": "Adventure paradise"},
                        {"name": "Japan", "code": "JP", "reason": "Cultural richness"}
                    ]
                    
                    cols = st.columns(3)
                    for idx, country in enumerate(generic_countries):
                        with cols[idx]:
                            st.markdown(f"""
                            <div class="destination-card">
                                <h3>🌍 {country['name']}</h3>
                                <p>Code: {country['code']}</p>
                                <p>{country['reason']}</p>
                            </div>
                            """, unsafe_allow_html=True)
            
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.info("💡 Tip: Make sure your API key is correct and 'complete_tarot_travel_database.json' is in the same directory.")

# Info section
st.markdown("---")
with st.expander("ℹ️ How it works"):
    st.markdown("""
    ### How Mystical Travel Planner Works
    
    1. **Draw a Card**: Click the button to draw a random tarot card from the RoxyAPI
    2. **Card Interpretation**: Each card (upright or reversed) has unique travel meanings
    3. **Country Matching**: Based on the card's energy, we recommend destinations that align with its symbolism
    4. **Plan Your Trip**: Use these insights to inspire your next adventure!
    
    **Database**: 78 tarot cards (22 Major Arcana + 56 Minor Arcana)  
    **Orientations**: Each card has different meanings upright vs. reversed  
    **Countries**: 150+ unique country recommendations with detailed reasons
    """)

# Footer
st.markdown("---")
st.markdown("*Powered by RoxyAPI Tarot & Custom Travel Database*")
