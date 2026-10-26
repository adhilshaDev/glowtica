from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Literal
import os


class DetectedProblem(BaseModel):
    name: str = Field(
        description="Name of concern: tanned, oily, uneven_tone, redness, acne, dark_circles, dullness, or visible_pores"
    )
    percentage: int = Field(description="Severity or prevalence percentage 0-100")


class SkinAnalysisResult(BaseModel):
    skin_type: Literal["dry", "normal", "oily", "combination", "sensitive", "uncertain"]
    skin_type_confidence_percentage: int = Field(description="Confidence score 0-100")
    detected_problems: List[DetectedProblem] = Field(
        description="Detected problems checked against skin concerns"
    )
    concern_notes: str = Field(
        description="1-2 sentence plain language summary of cosmetic observation"
    )


def analyze_skin_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Calls Gemini API (gemini-3.5-flash) to analyze a skin photo using structured Pydantic output.
    Returns a dictionary containing skin_type, confidence, top 4 detected_problems, and concern_notes.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not configured. "
            "Please add GEMINI_API_KEY=your_key_here to backend/.env"
        )

    client = genai.Client(api_key=api_key)

    prompt = (
        "You are a cosmetic skincare estimate assistant. Analyze this face/skin photo conservatively.\n"
        "DISCLAIMER & RULE: This is a cosmetic estimate tool ONLY, NOT a medical diagnosis. "
        "Avoid any clinical or medical diagnostic language.\n\n"
        "Tasks:\n"
        "1. Determine skin type: dry, normal, oily, combination, sensitive, or uncertain.\n"
        "2. Estimate skin_type_confidence_percentage as an integer (0 to 100).\n"
        "3. Evaluate skin concerns strictly from this list: tanned, oily, uneven_tone, redness, acne, dark_circles, dullness, visible_pores.\n"
        "   For each detected concern, provide its percentage (0 to 100).\n"
        "4. Write a 1-2 sentence plain language summary in concern_notes."
    )

    models_to_try = [
        os.getenv("GEMINI_MODEL"),
        "gemini-3.5-flash",
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash",
    ]
    candidate_models = []
    for m in models_to_try:
        if m and m not in candidate_models:
            candidate_models.append(m)

    response = None
    last_error = None

    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=SkinAnalysisResult,
                    temperature=0.2,
                ),
            )
            if response and response.parsed:
                break
        except Exception as err:
            last_error = err
            continue

    if not response or not response.parsed:
        if last_error:
            raise last_error
        raise ValueError("Failed to obtain structured output from Gemini API.")

    if not response.parsed:
        raise ValueError("Failed to obtain structured output from Gemini API.")

    result_dict = response.parsed.model_dump()

    # Return up to top 4 detected problems by percentage
    problems = result_dict.get("detected_problems", [])
    sorted_problems = sorted(problems, key=lambda p: p.get("percentage", 0), reverse=True)[:4]
    result_dict["detected_problems"] = sorted_problems

    return result_dict


class ProductSuitabilityResult(BaseModel):
    suitability_suggestion: str = Field(
        description="One sentence plain language cosmetic suitability suggestion for this product given the skin type."
    )


def generate_product_suitability(product_name: str, ingredients: str, skin_type: str) -> str:
    """
    Calls Gemini API to evaluate product suitability for a given skin type.
    Returns a single-sentence plain language cosmetic suggestion.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return f"This product is formatted for {skin_type} skin care."

    client = genai.Client(api_key=api_key)
    prompt = (
        f"You are a cosmetic skincare advisor.\n"
        f"Product Name: {product_name}\n"
        f"Key Ingredients: {ingredients or 'Standard formulation'}\n"
        f"User Skin Type: {skin_type}\n\n"
        "Provide a concise, exactly 1-sentence plain language cosmetic suitability advice for this user. "
        "Do NOT use medical or clinical diagnosis terms. Focus on cosmetic compatibility."
    )

    models_to_try = [
        os.getenv("GEMINI_MODEL"),
        "gemini-3.5-flash",
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash",
    ]
    candidate_models = []
    for m in models_to_try:
        if m and m not in candidate_models:
            candidate_models.append(m)

    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ProductSuitabilityResult,
                    temperature=0.2,
                ),
            )
            if response and response.parsed:
                return response.parsed.suitability_suggestion
        except Exception:
            continue

    return f"This product is compatible with {skin_type} skin routine."


class RoutineStep(BaseModel):
    step_number: int = Field(description="Order of step starting from 1")
    product_name: str = Field(description="Name of recommended or user product to apply")
    instruction: str = Field(description="Clear 1-2 sentence application instruction")


class RoutineGenerationResult(BaseModel):
    steps: List[RoutineStep] = Field(description="Ordered list of skincare routine steps")


def generate_skincare_routine(
    period: str,
    skin_type: str,
    top_problems: list,
    user_products: list,
    recommended_products: list
) -> list:
    """
    Calls Gemini API to generate an ordered AM/PM skincare routine.
    Returns a list of dictionaries with step_number, product_name, and instruction.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    user_prods_str = "\n".join([
        f"- {p.get('name')} ({p.get('type')}, timing: {p.get('timing')}): {p.get('ingredients', '')}"
        for p in user_products
    ]) if user_products else "None added"

    rec_prods_str = "\n".join([
        f"- {p.get('name')} ({p.get('brand')}, {p.get('category')}): {p.get('description')}"
        for p in recommended_products
    ]) if recommended_products else "None"

    problems_str = ", ".join([p.get("name", "") for p in top_problems]) if top_problems else "General skin maintenance"

    prompt = (
        f"You are a cosmetic skincare routine specialist.\n"
        f"Task: Create a personalized {period.upper()} (Morning/Evening) skincare routine.\n\n"
        f"USER PROFILE:\n"
        f"- Skin Type: {skin_type}\n"
        f"- Top Skin Concerns: {problems_str}\n\n"
        f"USER'S OWN PRODUCTS ({period.upper()} or Both):\n"
        f"{user_prods_str}\n\n"
        f"RECOMMENDED PRODUCTS FOR {skin_type.upper()} SKIN:\n"
        f"{rec_prods_str}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. Generate a logical {period.upper()} routine in chronological application order (e.g. Cleanser -> Serum -> Moisturizer -> Sunscreen for AM).\n"
        f"2. Incorporate the user's own products where suitable for {period.upper()}, supplemented by recommended products.\n"
        f"3. For each step, provide step_number (1, 2, 3...), product_name, and a 1-2 sentence application instruction.\n"
        f"4. Rule: Keep tone conservative and cosmetic-focused. Do NOT use medical diagnosis language."
    )

    models_to_try = [
        os.getenv("GEMINI_MODEL"),
        "gemini-3.5-flash",
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash",
    ]
    candidate_models = []
    for m in models_to_try:
        if m and m not in candidate_models:
            candidate_models.append(m)

    if api_key:
        client = genai.Client(api_key=api_key)
        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=RoutineGenerationResult,
                        temperature=0.2,
                    ),
                )
                if response and response.parsed:
                    steps_data = response.parsed.model_dump().get("steps", [])
                    return sorted(steps_data, key=lambda s: s.get("step_number", 1))
            except Exception:
                continue

    # Fallback routine if API unconfigured or unreachable
    if period.upper() == "AM":
        return [
            {"step_number": 1, "product_name": "Gentle Cleanser", "instruction": "Wash face with tepid water and gently pat dry with a clean towel."},
            {"step_number": 2, "product_name": "Hydrating Moisturizer", "instruction": "Apply a thin layer evenly across face and neck for daytime hydration."},
            {"step_number": 3, "product_name": "Broad-Spectrum Sunscreen SPF 50", "instruction": "Apply generously as the final morning step 15 minutes before sun exposure."}
        ]
    else:
        return [
            {"step_number": 1, "product_name": "Cleansing Gel", "instruction": "Thoroughly cleanse face to remove daily impurities and surface oils."},
            {"step_number": 2, "product_name": "Nourishing Night Cream", "instruction": "Smooth over face and neck before sleep to support skin moisture barrier overnight."}
        ]


