"""Local quiz and suggestions verification script for Zerofy India.

Demonstrates the hyper-personalized quiz generation and recommendations pipeline,
printing the exact prompts and Gemini responses to the terminal.
"""

import sys
import os
import dotenv
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
dotenv.load_dotenv()

# Import Firebase configuration and modules
from config.firebase import get_db
from utils.calculator import calculate_breakdown, CalculationError
from routes.quiz import _worst_category, _build_quiz_prompt, _parse_quiz_response
from utils.suggestion_engine import get_rule_based_suggestions, _build_polish_prompt, _parse_polish_response
from ai_client import generate_content


def verify_quiz_pipeline(db, user_id: str, state: str, profile_data: dict, log_data: dict):
    print(f"\n=================== QUIZ GENERATION PIPELINE FOR {profile_data.get('name')} ({profile_data.get('persona')}) ===================")
    
    # 1. Calculate Breakdown & find worst category
    try:
        breakdown = calculate_breakdown(log_data)
        worst_cat = _worst_category(breakdown)
        print(f"User's daily CO2 breakdown: {breakdown}")
        print(f"Worst habit category detected: '{worst_cat}' (Generates the most emissions)")
    except CalculationError as e:
        print(f"Error calculating breakdown: {e}")
        worst_cat = "diet"
        print(f"Fallback worst category: '{worst_cat}'")

    # 2. Build and print the quiz prompt
    prompt = _build_quiz_prompt(worst_cat)
    print("\n--- PROMPT SENT TO AI FOR QUIZ ---")
    print(prompt)
    print("--------------------------------------")

    # 3. Call AI
    try:
        api_key = os.environ["OPENROUTER_API_KEY"]
        
        print("\nCalling AI...")
        response_text = generate_content(prompt)
        print("\n--- RAW AI RESPONSES ---")
        print(response_text)
        print("----------------------------")
        
        # 4. Parse response
        parsed_quiz = _parse_quiz_response(response_text)
        print("\n-> Successfully parsed quiz questions:")
        for idx, q in enumerate(parsed_quiz):
            print(f"   Q{idx + 1}: {q['question']}")
            for opt_idx, opt in enumerate(q['options']):
                correct_marker = " [Correct ✅]" if opt_idx == q['correct_index'] else ""
                print(f"     ({opt_idx}) {opt}{correct_marker}")
            print(f"     Explanation: {q['explanation']}")
            
    except Exception as e:
        print(f"Quiz pipeline call failed: {e}")


def verify_suggestions_pipeline(db, user_id: str, profile_data: dict):
    print(f"\n=================== SUGGESTIONS GENERATION PIPELINE FOR {profile_data.get('name')} ===================")
    persona = profile_data.get("persona", "general")
    print(f"User profile details commuted: {profile_data.get('commute_mode')} for {profile_data.get('avg_daily_km')} km/day, AC: {profile_data.get('ac_hours_per_day')}h/day")
    
    # 1. Rule-based suggestions
    raw_sug = get_rule_based_suggestions(profile_data, persona)
    print("\n-> Rule-based suggestions (filtered by persona & current habits):")
    for idx, s in enumerate(raw_sug):
        print(f"   {idx + 1}. {s}")

    # 2. Build and print the polish prompt
    prompt = _build_polish_prompt(raw_sug, persona)
    print("\n--- PROMPT SENT TO GEMINI FOR POLISHING ---")
    print(prompt)
    print("-------------------------------------------")

    # 3. Call Gemini
    try:
        api_key = os.environ["OPENROUTER_API_KEY"]
        
        print("\nCalling AI...")
        response_text = generate_content(prompt)
        print("\n--- RAW AI RESPONSE ---")
        print(response_text)
        print("---------------------------")
        
        # 4. Parse response
        polished = _parse_polish_response(response_text)
        if polished:
            print("\n-> Final Polished Suggestions (Adapted for " + persona + " tone):")
            for idx, s in enumerate(polished):
                print(f"   {idx + 1}. {s}")
        else:
            print("\n-> Parsing failed: using unpolished rule-based suggestions instead.")
            
    except Exception as e:
        print(f"Suggestions pipeline call failed: {e}")


def main():
    print("=== Zerofy India Quiz & Suggestions NLP Test ===")
    
    try:
        db = get_db()
        print("Firestore Connected Successfully!")
    except Exception as e:
        print(f"Error: Firestore connection not available ({e}).")
        sys.exit(1)

    # Let's test using the Maharashtra users we seeded
    # Aarav Mehta ( महाराष्ट्र - heavy commute traveler - car commute)
    mh_user_id = "dummy_mh_1"
    mh_profile = db.collection("profiles").document(mh_user_id).get().to_dict()
    
    # Let's mock a daily log showing heavy car usage for today
    mh_log = {
        "user_id": mh_user_id,
        "date": date.today().isoformat(),
        "commute_mode": "petrol_car",
        "commute_km": 40.0,
        "ac_hours": 6.0,
        "diet_type": "non_vegetarian",
        "ac_hours_per_day": 6.0,
        "lpg_cylinders_per_month": 2.0
    }
    
    if mh_profile:
        # Run pipelines for Aarav
        verify_quiz_pipeline(db, mh_user_id, "Maharashtra", mh_profile, mh_log)
        verify_suggestions_pipeline(db, mh_user_id, mh_profile)
    else:
        print(f"Could not load profile for {mh_user_id}. Please seed the database first.")


if __name__ == "__main__":
    main()
