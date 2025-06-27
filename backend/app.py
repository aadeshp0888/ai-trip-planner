import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# --- Load .env ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DUMMY_MODE = os.getenv("DUMMY_MODE", "false").lower() == "true"

# --- Flask Setup ---
app = Flask(__name__)
CORS(app)

# --- LangChain Setup ---
if not DUMMY_MODE:
    try:
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import JsonOutputParser
        from langchain_openai import ChatOpenAI
        from langchain_core.pydantic_v1 import BaseModel, Field
        from typing import List

        # Define Output Schema
        class DayPlan(BaseModel):
            day: int = Field(description="Day number")
            activities: str = Field(description="Planned activities")
            food_recommendations: str = Field(description="Food suggestions")

        class TripPlan(BaseModel):
            destination: str = Field(description="Trip destination")
            itinerary: List[DayPlan] = Field(description="Day-wise itinerary")
            budget_breakdown: str = Field(description="Budget breakdown")
            transportation_suggestions: str = Field(description="Transport advice")

        # Load Model & Parser
        model = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo-0125", temperature=0.7)
        parser = JsonOutputParser(pydantic_object=TripPlan)

        # Prompt Template
        prompt_template = """
        You are a professional AI travel planner.
        Plan a {duration}-day trip to {destination} for a person with interests in {interests},
        budget level: {budget}, and preferred pace: {pace}.

        Provide:
        - Day-wise activities
        - Food suggestions
        - Budget breakdown
        - Transportation tips

        {format_instructions}
        """

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["destination", "duration", "budget", "interests", "pace"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        chain = prompt | model | parser

    except Exception as e:
        print(f"LangChain Init Error: {e}")
        sys.exit(1)

# --- API Endpoint ---
@app.route('/plan_trip', methods=['POST'])
def plan_trip():
    print("🔔 /plan_trip called")
    
    try:
        data = request.get_json(force=True)
        print("📥 Received:", data)

        # Basic validation
        for key in ['destination', 'duration', 'budget', 'interests', 'pace']:
            if key not in data or not data[key]:
                return jsonify({"error": f"Missing required field: {key}"}), 400

        # Dummy Mode Response
        if DUMMY_MODE:
            print("🧪 Dummy Mode Active")
            return jsonify({
                "destination": "Goa, India",
                "budget_breakdown": "Accommodation: ₹5000, Food: ₹2000, Activities: ₹1500",
                "transportation_suggestions": "Use local buses and rent scooters.",
                "itinerary": [
                    {"day": 1, "activities": "Beach relaxation and sunset at Baga", "food_recommendations": "Try local seafood thali"},
                    {"day": 2, "activities": "Visit Aguada Fort, Cruise at Mandovi", "food_recommendations": "Eat at Fisherman's Wharf"}
                ]
            })

        # Live OpenAI + LangChain Response
        response = chain.invoke({
            "destination": data["destination"],
            "duration": str(data["duration"]),
            "budget": data["budget"],
            "interests": data["interests"],
            "pace": data["pace"]
        })

        print("✅ LLM Response Ready")
        return jsonify(response)

    except Exception as e:
        print(f"❌ Internal Error: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# --- Run Flask ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
