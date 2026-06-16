"""Local chatbot integration and NLP verification script for Zerofy India.

Allows testing natural language messages locally to see how they are parsed
by Gemini and how the bot tone/preview card rules are applied.
"""

import sys
import os
from datetime import date
import dotenv

sys.path.insert(0, os.path.dirname(__file__))
dotenv.load_dotenv()

# Import configuration and parsing helpers
from config.firebase import get_db
from utils.gemini_parser import parse_user_message, ParseFailedError, build_parser_prompt
from ai_client import generate_content

def run_chat_input_test(message: str):
    print(f"\nUser says: '{message}'")
    try:
        # Generate and print the exact prompt sent to Gemini
        prompt = build_parser_prompt(message)
        print("=== PROMPT SENT TO AI ===")
        print(prompt)
        print("=============================")
        
        # Make the API call and get the raw response
        api_key = os.environ["OPENROUTER_API_KEY"]
        
        response_text = generate_content(prompt)
        print("\n=== RAW AI RESPONSE ===")
        print(response_text)
        print("===========================")
        
        # 1. Parsing NLP
        parsed_fields = parse_user_message(message)
        print("\n-> Parsed & Validated fields:")
        fields_found = False
        for k, v in parsed_fields.items():
            if v is not None:
                print(f"   * {k}: {v}")
                fields_found = True
        if not fields_found:
            print("   * None")
        
        # 2. Output Preview & Tone generation
        has_parsed_data = any(
            v is not None and (not isinstance(v, (int, float)) or v > 0)
            for k, v in parsed_fields.items()
        )
        
        confidence = "high" if has_parsed_data else "low"
        preview = None
        bot_reply = "Could you tell me a bit more?"
        
        if has_parsed_data:
            if parsed_fields.get("commute_mode"):
                mode = parsed_fields["commute_mode"]
                km = parsed_fields.get("avg_daily_km") or 0.0
                mode_str = mode.replace('_', ' ')
                emoji = "🚇" if mode == "metro" else "🚗" if "car" in mode or "vehicle" in mode else "🛵" if "wheeler" in mode else "🚌" if mode == "bus" else "🚶" if mode == "walking" else "🚲" if mode == "cycling" else "🚇"
                preview = {"category": "Transport", "change": mode, "quantity": km, "unit": "km"}
                qty_str = int(km) if km.is_integer() else km
                bot_reply = f"Got it — you switched to {mode_str} for {qty_str} km {emoji} Confirm?"
            elif parsed_fields.get("diet_type"):
                diet = parsed_fields["diet_type"]
                diet_str = diet.replace('_', ' ')
                preview = {"category": "Diet", "change": diet, "quantity": 1, "unit": "day"}
                bot_reply = f"Got it — you had a {diet_str} meal today? Confirm?"
            elif parsed_fields.get("ac_hours_per_day") is not None:
                ac = parsed_fields["ac_hours_per_day"]
                preview = {"category": "AC Usage", "change": "AC", "quantity": ac, "unit": "hours"}
                qty_str = int(ac) if ac.is_integer() else ac
                bot_reply = f"Got it — you used the AC for {qty_str} hours today ❄️ Confirm?"
            elif parsed_fields.get("lpg_cylinders_per_month") is not None:
                lpg = parsed_fields["lpg_cylinders_per_month"]
                preview = {"category": "LPG Cylinder", "change": "LPG", "quantity": lpg, "unit": "cylinders"}
                bot_reply = f"Got it — you used {lpg} LPG cylinders this month? Confirm?"

        print(f"-> Confidence: {confidence}")
        print(f"-> Bot response: \"{bot_reply}\"")
        if preview:
            print(f"-> Preview: {preview['category']} → {preview['change']} | {preview['quantity']} {preview['unit']}")
            
        return parsed_fields, confidence
        
    except ParseFailedError as e:
        print(f"-> Parsing failed: {e}")
        print("-> Bot response: \"Hmm, I didn't quite catch that — try the quick form below\"")
        return None, "low"
    except Exception as e:
        print(f"-> Error calling Gemini: {e}")
        return None, "low"

def main():
    print("=== Zerofy India Local Chatbot NLP Test ===")
    
    # Check Firestore connection
    try:
        db = get_db()
        print("Firestore Connected Successfully!")
    except Exception as e:
        print(f"Warning: Firestore connection not available ({e}). Running NLP test only.")

    test_messages = [
        "I took the metro today for 12km",
        "I skipped the AC today",
        "I had a vegan diet today"
    ]
    
    for msg in test_messages:
        run_chat_input_test(msg)
        print("-" * 80)

if __name__ == "__main__":
    main()
