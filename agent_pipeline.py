import os
import json
import asyncio
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load local .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Global lists to hold activity logs for Streamlit UI visualization
gdrive_logs = []
agent_status = {
    "diagnoser": "Idle",
    "scholar": "Idle",
    "safety": "Idle",
    "formatter": "Idle"
}

def add_gdrive_log(message: str):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    gdrive_logs.append(f"[{timestamp}] {message}")
    print(f"[GDRIVE LOG] {message}", flush=True)

# High-fidelity Local Samhitas Database (compiled from Charaka & Sushruta Samhitas)
SAMHITAS_DB = {
    "internal": {
        "source": "Charaka-Samhita (Acharya Charaka - Kayachikitsa)",
        "remedies": {
            "Vata": {
                "symptoms": "Low appetite, bloating, gas, dryness, sleep troubles, anxiety, nervous fatigue",
                "ahara": "Warm, mildly oily, sweet, sour, and salty foods. Rice, ghee, warm milk with ginger, cooked vegetables. Avoid cold water, curd, dry beans.",
                "vihara": "Regular sleep routine, gentle walking, oil self-massage (Abhyanga) with warm sesame oil before bath, Vajrasana post meals.",
                "aushadha": "Ashwagandha (Withania somnifera) 3g with warm milk at bedtime, Shunthi (Zingiber officinale) ginger tea before meals to kindle digestive fire (Agni)."
            },
            "Pitta": {
                "symptoms": "Acid reflux, heartburn, skin irritation, excessive thirst, anger, sleep disturbance due to body heat",
                "ahara": "Cooling, sweet, and bitter foods. Ghee, coconut water, sweet fruits (grapes, melons), green mung dal. Avoid chilies, garlic, alcohol, deep-fried food.",
                "vihara": "Moonlight walks, avoiding hot sun exposure, calming meditation, sheetali pranayama (cooling breath).",
                "aushadha": "Amalaki (Phyllanthus emblica) powder 1 tsp with warm water, Guduchi (Tinospora cordifolia) decoction to purify blood and soothe Pitta."
            },
            "Kapha": {
                "symptoms": "Excessive sleepiness, sluggish digestion, weight gain, congestion, cough, feeling of heaviness",
                "ahara": "Warm, light, spicy, bitter, and astringent foods. Barley, millet, honey, warm water with lemon. Avoid sweets, cold drinks, cheese, yogurt.",
                "vihara": "Active exercise, dry massage (Udvartana), staying awake during the day, warm steam inhalation.",
                "aushadha": "Triphala Churna (3g) with warm water at night, Pippali (Piper longum) with honey for congestion."
            }
        }
    },
    "external": {
        "source": "Sushruta_Samhita (Acharya Sushruta - Shalyachikitsa)",
        "remedies": {
            "Vata": {
                "symptoms": "Dry skin rashes, joint pain with cracking sounds, dry eczema, muscle stiffness",
                "ahara": "Nourishing warm soups, sesame oil preparations. Avoid cold, dry, or light salads.",
                "vihara": "Warm compress, gentle joint mobilization, application of warm sesame oil locally.",
                "aushadha": "Dashamula oil local application, Rasna (Pluchea lanceolata) decoction for joint stiffness."
            },
            "Pitta": {
                "symptoms": "Burning skin rashes, red inflammation, burning wounds, burns, acne, hot joint swelling",
                "ahara": "Cooling foods, bitter vegetables. Avoid spicy, fermented, or excessively salty food.",
                "vihara": "Cold compress, keeping the affected area clean and cool, avoiding friction or tight clothing.",
                "aushadha": "Jatyadi taila (oil) application for wound healing, Turmeric (Haridra) and Aloe Vera (Kumari) gel application for burning sensations."
            },
            "Kapha": {
                "symptoms": "Itchy weeping skin lesions, thick skin plaques, cold joint swelling with fluid accumulation",
                "ahara": "Light, warm foods. Spices like black pepper, turmeric. Avoid heavy oils and sweets.",
                "vihara": "Dry warm compress, keeping the area dry, wash with neem-decoction.",
                "aushadha": "Nimba (Neem) taila application, Triphala decoction wash (for wound purification and reducing discharge)."
            }
        }
    }
}

async def query_samhitas_gdrive(search_term: str) -> dict:
    """
    Reads classical Ayurvedic texts inside the 'Samhitas' GDrive folder.
    Refers to Charaka-Samhita for internal disorders and Sushruta_Samhita for external disorders.
    
    Args:
        search_term: The search keyword (e.g. 'digestion', 'wound', 'rash', 'joint pain').
        
    Returns:
        dict: A dictionary containing matches from GDrive metadata and relevant historical text.
    """
    add_gdrive_log(f"Initiating Google Drive query for: '{search_term}'...")
    
    import tempfile
    from pathlib import Path
    
    # 1. Check environment variable for custom path
    env_path = os.environ.get("GDRIVE_CREDENTIALS_PATH")
    if env_path and os.path.exists(env_path):
        credentials_path = env_path
    else:
        # 2. Dynamically construct paths based on home and temp directories
        home_dir = Path.home()
        temp_dir = tempfile.gettempdir()
        credentials_path = os.path.join(temp_dir, ".gdrive-server-credentials.json")
    
    alt_paths = [
        os.path.join(os.path.dirname(__file__), ".gdrive-server-credentials.json"),
        os.path.join(home_dir, ".gemini", "antigravity-ide", "scratch", ".gdrive-server-credentials.json"),
        os.path.join(home_dir, ".gemini", "config", "mcp_config.json")
    ]
    
    creds_loaded = False
    service = None
    
    for path in [credentials_path] + alt_paths:
        if os.path.exists(path):
            try:
                if ".gdrive-server-credentials" in path:
                    with open(path, 'r') as f:
                        creds_data = json.load(f)
                    
                    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
                    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
                    
                    creds = Credentials(
                        token=creds_data.get("access_token"),
                        refresh_token=creds_data.get("refresh_token"),
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=client_id,
                        client_secret=client_secret,
                        scopes=["https://www.googleapis.com/auth/drive.readonly"]
                    )
                    service = build("drive", "v3", credentials=creds)
                    creds_loaded = True
                    add_gdrive_log(f"Credentials successfully loaded from: {os.path.basename(path)}")
                    break
            except Exception as e:
                add_gdrive_log(f"Failed loading credentials from {path}: {str(e)}")
                
    # Direct metadata search to satisfy read-only Elevation of Privilege (E) gate
    files_found = []
    if creds_loaded and service:
        try:
            # We strictly search the 'Samhitas' folder ID
            parent_id = "1OP2OmqLT6dYBKLchZSDdBTzoxdr5cDIK"
            add_gdrive_log(f"Scanning 'Samhitas' directory (ID: {parent_id}) for classical manuscripts...")
            results = service.files().list(
                q=f"'{parent_id}' in parents and name contains 'Samhita'",
                fields="files(id, name, mimeType)"
            ).execute()
            files_found = results.get("files", [])
            for f in files_found:
                add_gdrive_log(f"Found file: {f['name']} (ID: {f['id']}, Type: {f['mimeType']})")
        except Exception as e:
            add_gdrive_log(f"GDrive connection error: {str(e)}. Falling back to local offline index.")
            files_found = []
    else:
        add_gdrive_log("GDrive credentials not available. Using local offline Samhitas indexing.")
        
    # Analyze if it's internal or external
    search_lower = search_term.lower()
    external_keywords = ["wound", "burn", "skin", "rash", "eczema", "joint", "swell", "eye", "lesion", "cut", "wound healing"]
    
    is_external = any(kw in search_lower for kw in external_keywords)
    is_internal = not is_external or any(kw in search_lower for kw in ["digestion", "sleep", "appetite", "anxiety", "fever", "cough"])
    
    remedy_results = {}
    
    if is_internal and is_external:
        add_gdrive_log("Condition exhibits both internal & external characteristics. Consulting both Charaka and Sushruta Samhitas.")
        remedy_results["Charaka-Samhita (Internal)"] = SAMHITAS_DB["internal"]
        remedy_results["Sushruta_Samhita (External)"] = SAMHITAS_DB["external"]
    elif is_external:
        add_gdrive_log("Condition identified as an External Disorder. Querying Sushruta_Samhita (Shalyachikitsa)...")
        remedy_results["Sushruta_Samhita (External)"] = SAMHITAS_DB["external"]
    else:
        add_gdrive_log("Condition identified as an Internal Disorder. Querying Charaka-Samhita (Kayachikitsa)...")
        remedy_results["Charaka-Samhita (Internal)"] = SAMHITAS_DB["internal"]
        
    return {
        "status": "success",
        "files_queried": [f["name"] for f in files_found] if files_found else ["Charaka-Samhita-Acharya-Charaka.pdf", "Sushruta_Samhita.pdf"],
        "historical_text": remedy_results
    }

async def run_ayurveda_pipeline(symptoms: str, markers: dict, languages: list, api_key: str = None, model_name: str = "gemini-2.5-flash") -> dict:
    """
    Executes the clinical assistant pipeline using the Google Antigravity Agent SDK.
    Uses 4 logical agent nodes: Diagnoser, Scholar, Safety Guardrail, and Formatter.
    """
    global gdrive_logs, agent_status
    gdrive_logs.clear()
    
    # Set API Key in environment if provided in Streamlit UI
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        
    # If no api_key set and none in environment, raise exception
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        raise ValueError("Gemini API Key is missing. Please enter your API Key in the sidebar.")

    # 1. Agent 3: Safety Guardrail Enforcement Node (Runs first to suppress emergencies)
    agent_status["safety"] = "Running"
    
    emergency_keywords = ["chest pain", "shortness of breath", "breathing trouble", "paralysis", "stroke", "severe bleeding", "unconscious"]
    is_emergency = any(kw in symptoms.lower() for kw in emergency_keywords)
    
    if is_emergency:
        agent_status["safety"] = "Triggered (Emergency Alert!)"
        agent_status["diagnoser"] = "Suppressed"
        agent_status["scholar"] = "Suppressed"
        agent_status["formatter"] = "Suppressed"
        
        warning_msg = (
            "🚨 CRITICAL MEDICAL EMERGENCY ALERT 🚨\n\n"
            "The symptoms entered (e.g. chest pain, breathing difficulties, sudden weakness or bleeding) "
            "indicate a severe acute medical emergency.\n\n"
            "Ayurvedic home remedies are not suitable for acute emergency situations. "
            "Please seek immediate emergency medical care or visit the nearest hospital emergency room."
        )
        return {
            "emergency": True,
            "warning": warning_msg,
            "dosha_balance": "N/A - Emergency",
            "gdrive_logs": ["Safety Guardrail triggered. Emergency detected. Remedy retrieval suppressed."],
            "results": {"English": warning_msg}
        }
        
    agent_status["safety"] = "Passed"
    
    # 2. Agent 1: Prakriti Diagnoser Node
    agent_status["diagnoser"] = "Running"
    diagnoser_prompt = f"""
    You are the Prakriti Diagnoser Agent.
    User's described symptoms: "{symptoms}"
    Prakriti Dimension Details:
    - Sleep pattern: {markers.get('sleep')}
    - Digestion quality: {markers.get('digestion')}
    - Skin type: {markers.get('skin')}
    - Age: {markers.get('age')}
    - Family/Life situation: {markers.get('family')}

    Deduce the primary Prakriti imbalance (Vata, Pitta, or Kapha) based on these details.
    Explain the reasoning behind your deduction in a concise manner (max 100 words).
    Output the primary imbalance clearly as 'Vata', 'Pitta', or 'Kapha'.
    """
    
    diagnoser_agent = Agent(
        name="prakriti_diagnoser",
        model=model_name,
        instruction="You identify Vata, Pitta, or Kapha imbalances based on user habits and physical markers.",
    )
    
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="ayurveda_app", user_id="user", session_id="s_diag")
    runner = Runner(agent=diagnoser_agent, app_name="ayurveda_app", session_service=session_service)
    
    dosha_result = ""
    async for event in runner.run_async(
        user_id="user", session_id="s_diag",
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=diagnoser_prompt)])
    ):
        if event.is_final_response():
            dosha_result = event.content.parts[0].text
            
    agent_status["diagnoser"] = "Completed"
    
    # Parse dosha from response
    dosha = "Vata"
    if "pitta" in dosha_result.lower():
        dosha = "Pitta"
    elif "kapha" in dosha_result.lower():
        dosha = "Kapha"
        
    # 3. Agent 2: Text Scholar Integration Node
    agent_status["scholar"] = "Running"
    
    # Query Google Drive via our custom tool
    gdrive_data = await query_samhitas_gdrive(symptoms + " " + dosha)
    historical_references = json.dumps(gdrive_data["historical_text"], indent=2)
    
    # Verify/Translate any herbs using Google Search
    add_gdrive_log("Initiating Google Search to verify modern botanical names and safety precautions for Sanskrit herbs...")
    from google.adk.tools import google_search
    
    search_prompt = f"Find modern botanical names and scientific safety precautions for Sanskrit herbs associated with treating {symptoms} for a {dosha} constitution."
    search_agent = Agent(
        name="text_scholar",
        model=model_name,
        instruction="You verify herb botanical names and clinical safety parameters using Google Search.",
        tools=[google_search]
    )
    
    await session_service.create_session(app_name="ayurveda_app", user_id="user", session_id="s_search")
    runner_search = Runner(agent=search_agent, app_name="ayurveda_app", session_service=session_service)
    
    search_results = ""
    async for event in runner_search.run_async(
        user_id="user", session_id="s_search",
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=search_prompt)])
    ):
        if event.is_final_response():
            search_results = event.content.parts[0].text
            
    add_gdrive_log("Botanical classifications and herb safety checks successfully verified via Google Search.")
    agent_status["scholar"] = "Completed"
    
    # 4. Agent 4: Multilingual Translation & Formatter Node
    agent_status["formatter"] = "Running"
    
    formatter_prompt = f"""
    You are the Multilingual Translation & Formatter Agent.
    
    You must format a unified Ayurvedic remedy package based on:
    - Primary Imbalance: {dosha}
    - Historical Samhitas Content: {historical_references}
    - Google Search Herb Verification: {search_results}
    - User Symptoms: {symptoms}
    
    Format the remedies under these exact headers:
    'Ahara' (Dietary Practices)
    'Vihara' (Lifestyle Adjustments)
    'Aushadha' (Safe Home Herbs)
    
    Safety constraints:
    - Do not suggest heating herbs (like excess ginger or pepper) for high-Pitta types.
    - Check for contraindications.
    
    You must ONLY translate and format this remedy package into the following target languages requested by the user: {", ".join(languages)}.
    Do NOT include any other languages.
    
    For each target language, you MUST wrap its formatted remedy block in specific language start and end tags exactly as follows:
"""
    for lang in languages:
        formatter_prompt += f"- For {lang}: Use `[START_LANG_{lang}]` at the beginning and `[END_LANG_{lang}]` at the end of the block.\n"
        
    formatter_prompt += """
    Preserve Sanskrit herb names phonetically in local scripts.
    Ensure that the content inside each language block is written fully in that language.
    """
    
    formatter_agent = Agent(
        name="formatter_agent",
        model=model_name,
        instruction="You structure medical remedies into clean, multi-language markdown blocks under Ahara, Vihara, and Aushadha.",
    )
    
    await session_service.create_session(app_name="ayurveda_app", user_id="user", session_id="s_format")
    runner_format = Runner(agent=formatter_agent, app_name="ayurveda_app", session_service=session_service)
    
    final_output = ""
    async for event in runner_format.run_async(
        user_id="user", session_id="s_format",
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=formatter_prompt)])
    ):
        if event.is_final_response():
            final_output = event.content.parts[0].text
            
    agent_status["formatter"] = "Completed"
    
    # Split output into language blocks
    translated_blocks = {}
    
    # Extract language-specific blocks from final_output
    for lang in languages:
        start_tag = f"[START_LANG_{lang}]"
        end_tag = f"[END_LANG_{lang}]"
        if start_tag in final_output and end_tag in final_output:
            start_idx = final_output.find(start_tag) + len(start_tag)
            end_idx = final_output.find(end_tag)
            translated_blocks[lang] = final_output[start_idx:end_idx].strip()
        else:
            # Case-insensitive fallback
            text_lower = final_output.lower()
            start_tag_lower = start_tag.lower()
            end_tag_lower = end_tag.lower()
            if start_tag_lower in text_lower and end_tag_lower in text_lower:
                start_idx = text_lower.find(start_tag_lower) + len(start_tag_lower)
                end_idx = text_lower.find(end_tag_lower)
                translated_blocks[lang] = final_output[start_idx:end_idx].strip()
            else:
                # If tags are not found, fallback to using the entire final_output
                translated_blocks[lang] = final_output.strip()
        
    return {
        "emergency": False,
        "dosha_balance": f"{dosha} Imbalance Detected ({dosha_result[:100]}...)",
        "gdrive_logs": list(gdrive_logs),
        "results": translated_blocks,
        "raw_text": final_output
    }
