import streamlit as st
import requests
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="Smart AI Trip Planner",
    page_icon="✈️",
    layout="wide"
)

# --- Backend API URL ---
# CRITICAL: This URL must point to your locally running Flask backend.
BACKEND_URL = "http://localhost:5000/plan_trip"


# --- Helper Function to Display the Plan ---
def display_trip_plan(plan):
    st.header(f"Your Trip to {plan.get('destination', 'your destination')}")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💰 Budget Breakdown")
        st.write(plan.get('budget_breakdown', 'No budget information available.'))

    with col2:
        st.subheader("🚌 Transportation")
        st.write(plan.get('transportation_suggestions', 'No transportation information available.'))

    st.divider()

    st.subheader("🗓️ Daily Itinerary")
    itinerary = plan.get('itinerary', [])
    if not itinerary:
        st.warning("No itinerary was generated.")
        return

    for day_plan in itinerary:
        with st.expander(f"**Day {day_plan.get('day', 'N/A')}**"):
            st.markdown("##### 🚶‍♂️ Activities")
            st.write(day_plan.get('activities', 'No activities planned.'))
            st.markdown("##### 🍽️ Food Recommendations")
            st.write(day_plan.get('food_recommendations', 'No food recommendations.'))


# --- Main UI ---
st.title("Smart AI Trip Planner ✈️")
st.write("Fill in your travel preferences and let AI create a personalized itinerary for you!")

with st.sidebar:
    st.header("Your Travel Preferences")
    destination = st.text_input("📍 Destination (e.g., Paris, France)")
    duration = st.number_input("⏳ Duration (in days)", min_value=1, max_value=30, value=7)
    budget = st.select_slider(
        "💵 Budget",
        options=["Economy", "Standard", "Luxury"],
        value="Standard"
    )
    interests = st.text_area("🎨 Interests (e.g., art, history, hiking, nightlife)")
    pace = st.radio(
        "🏃 Pace",
        options=["Relaxed", "Moderate", "Fast-Paced"],
        index=1,
        horizontal=True
    )

    plan_button = st.button("Plan My Trip!", use_container_width=True, type="primary")

# --- Logic to call backend and display results ---
if plan_button:
    if not destination or not interests:
        st.error("Please fill in the Destination and Interests fields.")
    else:
        with st.spinner("🤖 Our AI is crafting your perfect trip... This may take a moment."):
            try:
                payload = {
                    "destination": destination,
                    "duration": duration,
                    "budget": budget,
                    "interests": interests,
                    "pace": pace
                }
                
                response = requests.post(BACKEND_URL, json=payload, timeout=120) # 120-second timeout
                response.raise_for_status()  # Raises an exception for 4XX/5XX errors
                
                trip_plan = response.json()
                st.session_state['trip_plan'] = trip_plan # Save the plan to session state

            except requests.exceptions.RequestException as e:
                st.error(f"Network error: Failed to connect to the backend. Is it running? Details: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                # Try to print the raw response if available for debugging
                if 'response' in locals() and response.text:
                    st.error(f"Backend raw response: {response.text}")

# Display the plan if it exists in the session state
if 'trip_plan' in st.session_state:
    display_trip_plan(st.session_state['trip_plan'])