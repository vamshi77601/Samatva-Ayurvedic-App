import asyncio
import os
import sys
from dotenv import load_dotenv

# Reconfigure stdout to use utf-8 to avoid Windows console encoding errors (charmap)
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Load env variables from .env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Import pipeline
sys.path.append(os.path.dirname(__file__))
from agent_pipeline import run_ayurveda_pipeline

async def test_normal_flow():
    print("=========================================")
    print("TESTING NORMAL PIPELINE FLOW")
    print("=========================================")
    symptoms = "I have experienced strong indigestion, bloating after eating, and dry skin lately."
    markers = {
        "sleep": "Light / Interrupted",
        "digestion": "Irregular / Gas-prone",
        "skin": "Dry / Rough / Thin",
        "age": 32,
        "family": "Moderate stress, corporate employee"
    }
    languages = ["English"]
    
    print(f"Symptoms: {symptoms}")
    print(f"Markers: {markers}")
    print("Running pipeline...")
    
    try:
        results = await run_ayurveda_pipeline(symptoms, markers, languages)
        print("\nPipeline Result:")
        print("Dosha deduction:", results["dosha_balance"])
        print("\nGDrive Scholar Logs:")
        for log in results["gdrive_logs"]:
            print(f"- {log}")
            
        print("\nFinal Remedy Output (English Excerpt):")
        english_out = results["results"]["English"]
        print(english_out[:400] + "...")
        print("\nNormal flow test SUCCESS!")
    except Exception as e:
        print("\nNormal flow test FAILED as expected (invalid user key):", str(e))

async def test_emergency_flow():
    print("\n=========================================")
    print("TESTING EMERGENCY CRITICAL GATE FLOW")
    print("=========================================")
    symptoms = "My grandfather is having severe chest pain and sudden shortness of breath."
    markers = {
        "sleep": "Sound / Good",
        "digestion": "Balanced / Regular",
        "skin": "Normal / Healthy",
        "age": 78,
        "family": "High anxiety"
    }
    languages = ["English"]
    
    print(f"Symptoms: {symptoms}")
    print("Running pipeline...")
    
    try:
        results = await run_ayurveda_pipeline(symptoms, markers, languages)
        print("\nPipeline Result:")
        print("Dosha deduction:", results["dosha_balance"])
        print("Is Emergency:", results.get("emergency"))
        print("\nGDrive Scholar Logs:")
        for log in results["gdrive_logs"]:
            print(f"- {log}")
            
        print("\nFinal Output Warning:")
        print(results["results"]["English"])
        print("\nEmergency flow test SUCCESS!")
    except Exception as e:
        print("\nEmergency flow test FAILED:", str(e))

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GEMINI_API_KEY not configured in F:/agy-cli-projects/ayurveda_app/.env")
        sys.exit(1)
        
    asyncio.run(test_normal_flow())
    asyncio.run(test_emergency_flow())
