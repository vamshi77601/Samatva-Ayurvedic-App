import streamlit as st
import os
import asyncio
from utils import validate_input, log_transaction, inject_custom_css
from articles import ARTICLES
from agent_pipeline import run_ayurveda_pipeline, agent_status

# Page Configuration
st.set_page_config(
    page_title="Samatva Ayurvedic Health Assistant",
    page_icon="📜",
    layout="wide"
)

# Inject Neumorphic / 3D styling
inject_custom_css()

# App Header
st.markdown("""
    <div style="text-align: center; padding: 0 0 30px 0;">
        <span class="badge-saffron" style="font-size: 1.1rem; padding: 8px 20px; margin-bottom: 15px;">
            🪔 Samatva Ayurvedic Health Assistant
        </span>
        <h1 style="font-size: 3rem; margin-top: 10px; margin-bottom: 5px; color: #2E5A44;">
            🍃Bharat Ayurvedic Health Remedies
        </h1>
        <p style="font-size: 1.2rem; color: #555; max-width: 800px; margin: 0 auto;">
            A clinical reasoning system mapping modern symptoms to classical Ayurvedic Samhitas  
        </p>
    </div>
""", unsafe_allow_html=True)

# Sidebar Configuration (API Key & Instructions)
st.sidebar.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <span class="badge-emerald" style="font-size: 1rem; width: 70%;">
            ⚙️ Settings
        </span>
    </div>
""", unsafe_allow_html=True)

# Model selection
model_options = ["gemini-2.5-flash", "gemini-2.5-pro", "Gemini 3.5 Low", "Gemini 3.5 Medium", "Gemini 3.1"]
selected_model_label = st.sidebar.selectbox(
    "Select Gemini Model:",
    options=model_options,
    index=0,
    help="Select the Gemini model to use for the multi-agent council."
)

model_mapping = {
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-2.5-pro": "gemini-2.5-pro",
    "Gemini 3.5 Low": "gemini-3.5-flash",
    "Gemini 3.5 Medium": "gemini-3.5-flash",
    "Gemini 3.1": "gemini-3.1-flash-lite"
}
selected_model = model_mapping[selected_model_label]

st.sidebar.markdown("""
    <div style="margin-top: 30px;" class="neumorphic-card">
        <h4 style="color: #2E5A44; font-weight: 600; margin-bottom: 10px;">Clinical Scopes</h4>
        <p style="font-size: 0.9rem; color: #555; line-height: 1.4;">
            <b>Charaka-Samhita:</b> Utilized for diagnosing and recommending remedies for <i>Internal Disorders</i> (Kayachikitsa).<br><br>
            <b>Sushruta-Samhita:</b> Utilized for diagnosing and recommending remedies for <i>External Disorders</i> (Shalyachikitsa).
        </p>
    </div>
""", unsafe_allow_html=True)

# Main Application Tabs
tab1, tab2 = st.tabs(["🌿🩺 𝐏𝐫𝐚𝐤𝐫𝐢𝐭𝐢 𝐂𝐨𝐧𝐬𝐮𝐥𝐭𝐚𝐧𝐭", "🍂 𝐀𝐲𝐮𝐫𝐯𝐞𝐝𝐢𝐜 𝐔𝐩𝐝𝐚𝐭𝐞𝐬"])

with tab1:
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <p style="color: #000000; font-weight: bold; font-size: 1rem;">Describe your symptoms and physical dimensions to receive Samhita-grounded remedies.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Form layout inside a Neumorphic Card
    #st.markdown('<div class="neumorphic-card">', unsafe_allow_html=True)
    
    col_sym, col_mark = st.columns([2, 1.2])
    
    with col_sym:
        symptoms_input = st.text_area(
            "Describe your symptoms / health issues in detail:",
            placeholder="E.g., I have been experiencing indigestion, bloating, and poor appetite after meals for the past week, along with difficulty falling asleep...",
            height=180
        )
        
        # Multilingual Checkbox layout
        st.markdown("<p style='font-weight: 600; margin-bottom: 5px; color: #2E5A44;'>Target Multilingual Outputs</p>", unsafe_allow_html=True)
        col_l1, col_l2, col_l3, col_l4 = st.columns(4)
        with col_l1:
            lang_en = st.checkbox("English [EN]", value=True)
        with col_l2:
            lang_hi = st.checkbox("हिन्दी [HI]", value=False)
        with col_l3:
            lang_te = st.checkbox("తెలుగు [TE]", value=False)
        with col_l4:
            lang_ka = st.checkbox("ಕನ್ನಡ [KA]", value=False)
            
    with col_mark:
        st.markdown("<p style='font-weight: 600; margin-bottom: 5px; color: #2E5A44;'>Prakriti Baseline Markers</p>", unsafe_allow_html=True)
        sleep_marker = st.selectbox("Sleep Quality:", ["Light / Interrupted", "Moderate / Dreamy", "Heavy / Deep", "Sound / Good"])
        digestion_marker = st.selectbox("Digestion Speed:", ["Irregular / Gas-prone", "Strong / High thirst", "Slow / Heavy-feeling", "Balanced / Regular"])
        skin_marker = st.selectbox("Skin Texture:", ["Dry / Rough / Thin", "Warm / Acne-prone / Fair", "Oily / Smooth / Thick", "Normal / Healthy"])
        age_marker = st.number_input("Age:", min_value=1, max_value=120, value=30)
        family_marker = st.text_input("Life / Family Situation (Stress level):", placeholder="E.g., High stress corporate job, nuclear family")
        
    #st.markdown('</div>', unsafe_allow_html=True)
    
    # Languages mapping
    languages_selected = []
    if lang_en: languages_selected.append("English")
    if lang_hi: languages_selected.append("हिन्दी [HI]")
    if lang_te: languages_selected.append("తెలుగు [TE]")
    if lang_ka: languages_selected.append("ಕನ್ನಡ [KA]")
    
    # Generate button
    if st.button("Generate Guided Remedies 🪔"):
        if not symptoms_input.strip():
            st.error("Please describe your symptoms first.")
        elif not languages_selected:
            st.error("Please select at least one target output language.")
        else:
            # 1. STRIDE Security Check: Tampering & DoS
            log_transaction("Input validation gate triggered.")
            is_valid, validation_msg = validate_input(symptoms_input)
            
            if not is_valid:
                st.error(validation_msg)
            else:
                # Log transaction boundary
                log_transaction(f"Input Validated (Length: {len(symptoms_input)}) -> GDrive Query Fired")
                
                # Gather Prakriti markers
                markers = {
                    "sleep": sleep_marker,
                    "digestion": digestion_marker,
                    "skin": skin_marker,
                    "age": age_marker,
                    "family": family_marker
                }
                
                with st.spinner("Orchestrating Ayurvedic Multi-Agent Council..."):
                    try:
                        # Run pipeline
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        results = loop.run_until_complete(
                            run_ayurveda_pipeline(symptoms_input, markers, languages_selected, model_name=selected_model)
                        )
                        log_transaction("Safety Check Passed -> Remedy Retrieval Succeeded")
                        
                        # 2. Side-by-side Multi-Agent Visualization columns
                        st.markdown("<h3 style='margin-top: 30px; margin-bottom: 15px;'>🛡️ Multi-Agent Council Activity</h3>", unsafe_allow_html=True)
                        
                        col_a1, col_a2, col_a3 = st.columns(3)
                        
                        with col_a1:
                            st.markdown(f"""
                                <div class="neumorphic-card" style="min-height: 250px;">
                                    <span class="badge-saffron">Node 1: Diagnoser</span>
                                    <h4 style="margin-top: 15px; margin-bottom: 5px;">Prakriti Deduction</h4>
                                    <p style="font-size: 0.95rem; color: #333;">{results.get('dosha_balance')}</p>
                                    <hr style="margin: 10px 0;">
                                    <span class="badge-gold">Status: {agent_status['diagnoser']}</span>
                                </div>
                            """, unsafe_allow_html=True)
                            
                        with col_a2:
                            logs_html = "".join([f"<li style='font-size: 0.85rem; color: #666;'>{log}</li>" for log in results.get('gdrive_logs', [])])
                            st.markdown(f"""
                                <div class="neumorphic-card" style="min-height: 250px; overflow-y: auto;">
                                    <span class="badge-emerald">Node 2: Text Scholar</span>
                                    <h4 style="margin-top: 15px; margin-bottom: 5px;">GDrive & Search Logs</h4>
                                    <ul style="padding-left: 15px; margin-top: 10px;">
                                        {logs_html or '<li>No GDrive logs generated</li>'}
                                    </ul>
                                    <span class="badge-gold">Status: {agent_status['scholar']}</span>
                                </div>
                            """, unsafe_allow_html=True)
                            
                        with col_a3:
                            safety_text = "PASSED: All safety gates validated. Home remedies are safe for presentation."
                            safety_class = "badge-emerald"
                            if results.get("emergency"):
                                safety_text = "CRITICAL WARNING: Severe acute emergency detected! Suppression initiated."
                                safety_class = "badge-saffron"
                                
                            st.markdown(f"""
                                <div class="neumorphic-card" style="min-height: 250px;">
                                    <span class="{safety_class}">Node 3: Safety Guardrail</span>
                                    <h4 style="margin-top: 15px; margin-bottom: 5px;">STRIDE Validation</h4>
                                    <p style="font-size: 0.95rem; color: #333;">{safety_text}</p>
                                    <hr style="margin: 10px 0;">
                                    <span class="badge-gold">Status: {agent_status['safety']}</span>
                                </div>
                            """, unsafe_allow_html=True)
                            
                        # 3. Final Results UI
                        if results.get("emergency"):
                            st.markdown(f"""
                                <div style="background-color: #ffcccc; border-left: 6px solid #cc0000; padding: 25px; border-radius: 12px; margin-top: 25px;">
                                    <h3 style="color: #cc0000; margin-top:0;">⚠️ Medical Emergency Warning</h3>
                                    <p style="font-size: 1.1rem; color: #800000; white-space: pre-line;">{results.get('warning')}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("<h3 style='margin-top: 30px; margin-bottom: 15px;'>🌿 Grounded Ayurvedic Prescriptions</h3>", unsafe_allow_html=True)
                            
                            # Render sub-tabs for each language
                            lang_tabs = st.tabs(languages_selected)
                            for i, lang in enumerate(languages_selected):
                                with lang_tabs[i]:
                                    #st.markdown(f'<div class="neumorphic-card">', unsafe_allow_html=True)
                                    # Output translation text
                                    st.markdown(results["results"].get(lang, "No output generated for this language."))
                                    #st.markdown('</div>', unsafe_allow_html=True)
                                    
                    except Exception as e:
                        st.error(f"Error during council execution: {str(e)}")

with tab2:
    st.markdown("""
        <div style="margin-bottom: 25px;">
            <h2 style="color: #2E5A44; margin-bottom: 5px;">📰 Modern Practitioner Updates</h2>
            <p style="color: #666; font-size: 1rem;">Seasonal routines, Ministry of AYUSH updates, and CCRAS clinical trial briefs.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Render static article feed
    for art in ARTICLES:
        st.markdown(f"""
            <div class="article-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span class="badge-gold">{art['badge']}</span>
                    <span class="article-meta">{art['date']} | Written by {art['author']}</span>
                </div>
                <h3 class="article-title">{art['title']}</h3>
                <p style="color: #444; font-size: 0.98rem; line-height: 1.5; margin-top: 10px;">{art['summary']}</p>
            </div>
        """, unsafe_allow_html=True)
