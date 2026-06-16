"""Database verification and seeding script for Zerofy India leaderboard.

Validates connectivity to Firestore and populates top state-wise players
to prevent the leaderboard page from appearing empty.
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))

# Import configuration and firebase helpers
from config.firebase import get_db
from firebase_admin import firestore


def run_seeding():
    print("=== Zerofy India Firestore Connection & Seeding ===")
    
    try:
        print("Connecting to Firestore...")
        db = get_db()
        print("Connected successfully!")
    except Exception as e:
        print(f"Error connecting to Firebase: {e}")
        print("Please check your FIREBASE_CREDENTIALS_PATH in backend/.env")
        sys.exit(1)

    # 1. Connection check write-read test
    print("\nRunning write-read connectivity test...")
    try:
        test_ref = db.collection("connectivity_test").document("test_doc")
        test_ref.set({"status": "connected", "timestamp": firestore.SERVER_TIMESTAMP})
        
        doc = test_ref.get()
        if doc.exists and doc.to_dict().get("status") == "connected":
            print("Successfully verified database write and read operations!")
            # Clean up test document
            test_ref.delete()
        else:
            print("Write-read test failed: document content mismatch.")
            sys.exit(1)
    except Exception as e:
        print(f"Write-read connectivity test failed: {e}")
        sys.exit(1)

    # 2. Seed leaderboard data
    print("\nSeeding leaderboard dummy data...")
    today_str = date.today().isoformat()
    
    # 5 States with 3-4 users each
    states_data = {
        "Maharashtra": [
            {"uid": "dummy_mh_1", "name": "Aarav Mehta", "points": 120, "weekly_score": 90, "badges": ["Quiz Master", "First Step"]},
            {"uid": "dummy_mh_2", "name": "Devika Sharma", "points": 95, "weekly_score": 70, "badges": ["Week Warrior", "First Step"]},
            {"uid": "dummy_mh_3", "name": "Kabir Kapoor", "points": 80, "weekly_score": 50, "badges": ["Carbon Cutter", "First Step"]},
            {"uid": "dummy_mh_4", "name": "Zara Sen", "points": 75, "weekly_score": 40, "badges": ["First Step"]},
        ],
        "Delhi": [
            {"uid": "dummy_dl_1", "name": "Neha Gupta", "points": 130, "weekly_score": 100, "badges": ["Quiz Master", "Week Warrior", "First Step"]},
            {"uid": "dummy_dl_2", "name": "Rohan Dixit", "points": 90, "weekly_score": 60, "badges": ["First Step"]},
            {"uid": "dummy_dl_3", "name": "Simran Kaur", "points": 75, "weekly_score": 45, "badges": ["Carbon Cutter"]},
        ],
        "Karnataka": [
            {"uid": "dummy_ka_1", "name": "Rahul Nair", "points": 140, "weekly_score": 110, "badges": ["Quiz Master", "Week Warrior"]},
            {"uid": "dummy_ka_2", "name": "Priya Rao", "points": 105, "weekly_score": 80, "badges": ["Carbon Cutter", "First Step"]},
            {"uid": "dummy_ka_3", "name": "Vikram Shenoy", "points": 60, "weekly_score": 35, "badges": ["First Step"]},
        ],
        "Tamil Nadu": [
            {"uid": "dummy_tn_1", "name": "Karthik Raja", "points": 115, "weekly_score": 85, "badges": ["Week Warrior", "First Step"]},
            {"uid": "dummy_tn_2", "name": "Ananya Iyer", "points": 100, "weekly_score": 75, "badges": ["Quiz Master"]},
            {"uid": "dummy_tn_3", "name": "Venkatesh S", "points": 70, "weekly_score": 45, "badges": ["First Step"]},
        ],
        "Telangana": [
            {"uid": "dummy_tg_1", "name": "Srinivas Rao", "points": 125, "weekly_score": 95, "badges": ["Quiz Master", "Carbon Cutter"]},
            {"uid": "dummy_tg_2", "name": "Lakshmi K", "points": 85, "weekly_score": 55, "badges": ["First Step"]},
            {"uid": "dummy_tg_3", "name": "Abhinav Reddy", "points": 65, "weekly_score": 30, "badges": ["First Step"]},
        ]
    }

    try:
        for state, users in states_data.items():
            print(f"  Seeding users for {state}...")
            for u in users:
                # 2a. Profiles collection
                profile_ref = db.collection("profiles").document(u["uid"])
                profile_ref.set({
                    "name": u["name"],
                    "state": state,
                    "city": "Smart City",
                    "commute_mode": "metro",
                    "avg_daily_km": 12.0,
                    "diet_type": "vegetarian",
                    "ac_hours_per_day": 3.0,
                    "monthly_electricity_units": 150.0,
                    "lpg_cylinders_per_month": 1.0,
                    "persona": "student"
                })

                # 2b. Gamification collection
                gam_ref = db.collection("gamification").document(u["uid"])
                gam_ref.set({
                    "streak": len(u["badges"]) * 2 or 1,
                    "points": u["points"],
                    "weekly_score": float(u["weekly_score"]),
                    "badges": u["badges"],
                    "last_active_date": today_str,
                    "lifetime_logs": 5,
                    "state": state
                })
        print("Seeding finished successfully!")
    except Exception as e:
        print(f"Error seeding data: {e}")
        sys.exit(1)

    # 3. Test Query Execution (Validate fetching)
    print("\nValidating leaderboard query fetch from Firestore...")
    try:
        test_state = "Maharashtra"
        query = db.collection("gamification") \
                  .where("state", "==", test_state) \
                  .order_by("weekly_score", direction=firestore.Query.DESCENDING) \
                  .limit(50)
        docs = query.get()

        print(f"Query returned {len(docs)} documents for {test_state}:")
        for idx, doc in enumerate(docs):
            data = doc.to_dict()
            profile = db.collection("profiles").document(doc.id).get().to_dict() or {}
            print(f"  {idx + 1}. {profile.get('name')} | Weekly score: {data.get('weekly_score')} | Total points: {data.get('points')} | State: {data.get('state')}")
        
        print("\nLeaderboard query validation passed successfully!")
    except Exception as e:
        print(f"Error executing test query: {e}")
        print("Note: If you get a 'Google Cloud Firestore Index Required' error, click the link in the error to create the index.")
        sys.exit(1)

    print("\n=======================================================")
    print("Database connection verified and dummy data seeded successfully!")
    print("=======================================================")


if __name__ == "__main__":
    run_seeding()
