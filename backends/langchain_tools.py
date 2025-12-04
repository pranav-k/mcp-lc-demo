"""
LangChain tools for C360 retail demo.
These tools work alongside Voicebox to enable multi-tool agent workflows.
"""

import logging

from langchain_core.tools import tool

logging.basicConfig(level=logging.INFO)

# ============================================================================
# Language Tools
# ============================================================================

@tool
def detect_language(text: str) -> str:
    """
    Detect the language of the given text.
    Returns: Language name (English, Spanish, or German)

    Simple heuristic-based detection for demo purposes.
    """
    logging.info(f"TOOL CALL - detect_language: {text}")
    # Simple keyword-based detection for demo
    spanish_keywords = ['qué', 'cuál', 'cuáles', 'cómo', 'dónde', 'por', 'para', 'el', 'la', 'los', 'las', 'lista', 'productos', 'producto']
    german_keywords = ['wie', 'was', 'wo', 'der', 'die', 'das', 'und', 'für', 'über']

    text_lower = text.lower()

    spanish_count = sum(1 for keyword in spanish_keywords if keyword in text_lower)
    german_count = sum(1 for keyword in german_keywords if keyword in text_lower)

    if spanish_count > 0:
        return "Spanish"
    elif german_count > 0:
        return "German"
    else:
        return "English"


@tool
def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate text between languages using deep-translator (free API).
    Falls back to mock translations if API is unavailable.

    Args:
        text: Text to translate
        source_lang: Source language (English, Spanish, German)
        target_lang: Target language (English, Spanish, German)

    Returns: Translated text
    """
    logging.info(f"TOOL CALL - translate_text: {text[:50]}... [{source_lang} → {target_lang}]")

    if source_lang == target_lang:
        return text

    # Language name to code mapping for deep-translator
    lang_to_code = {
        "English": "en",
        "Spanish": "es",
        "German": "de"
    }

    try:
        # Try using deep-translator (free, no API key needed!)
        from deep_translator import GoogleTranslator

        source_code = lang_to_code.get(source_lang, "auto")
        target_code = lang_to_code.get(target_lang, "en")

        translator = GoogleTranslator(source=source_code, target=target_code)
        translated = translator.translate(text)

        logging.info(f"✓ Translation successful via deep-translator")
        return translated

    except ImportError:
        logging.warning("deep-translator not installed, using fallback mock translations")
        # Fallback to mock translations if deep-translator not installed
        return _mock_translate(text, source_lang, target_lang)
    except Exception as e:
        logging.warning(f"Translation API failed: {e}, using fallback")
        # Fallback to mock if API fails
        return _mock_translate(text, source_lang, target_lang)


def _mock_translate(text: str, source_lang: str, target_lang: str) -> str:
    """Fallback mock translations for demo (backup if API fails)"""
    translations = {
        ("Spanish", "English"): {
            "¿Cuáles son los mejores productos?": "What are the best products?",
            "¿Cuál es el total de pedidos?": "What is the total of orders?",
            "Lista de 5 productos populares": "List of 5 popular products",
            "Muéstrame los clientes principales": "Show me the top customers",
        },
        ("English", "Spanish"): {
            "The top products are": "Los mejores productos son",
            "The total is": "El total es",
            "Here are the results": "Aquí están los resultados",
        },
        ("German", "English"): {
            "Was sind die besten Produkte?": "What are the best products?",
            "Zeige mir die Top-Kunden": "Show me the top customers",
        }
    }

    # Try exact match first
    key = (source_lang, target_lang)
    if key in translations and text in translations[key]:
        return translations[key][text]

    # Fallback: return with note
    return f"[Translation {source_lang}→{target_lang}]: {text}"


# ============================================================================
# Shipping & Distance Tools
# ============================================================================

@tool
def calculate_distance(location1: str, location2: str) -> float:
    """
    Calculate estimated distance between two locations in miles.

    Args:
        location1: First location (city or address)
        location2: Second location (city or address)

    Returns: Distance in miles

    NOTE: This is a mock implementation using city-to-city estimates.
    In production, use a real geolocation API (Google Maps, MapBox, etc.)
    """
    logging.info(f"TOOL CALL - calculate_distance: {location1} {location2}")
    # Mock distances for common US cities for demo
    city_distances = {
        ("Los Angeles", "San Francisco"): 383,
        ("Los Angeles", "San Diego"): 120,
        ("Los Angeles", "Las Vegas"): 270,
        ("San Francisco", "Los Angeles"): 383,
        ("San Francisco", "Sacramento"): 88,
        ("San Francisco", "San Jose"): 48,
        ("New York", "Boston"): 215,
        ("New York", "Philadelphia"): 95,
        ("Chicago", "Detroit"): 283,
        ("Chicago", "Milwaukee"): 92,
    }

    # Normalize city names
    loc1 = location1.strip().title()
    loc2 = location2.strip().title()

    # Check both directions
    key = (loc1, loc2)
    reverse_key = (loc2, loc1)

    if key in city_distances:
        return city_distances[key]
    elif reverse_key in city_distances:
        return city_distances[reverse_key]
    else:
        # Fallback: random estimate for demo
        return 250.0  # Default moderate distance


@tool
def calculate_shipping_cost(distance_miles: float, order_value: float) -> dict:
    """
    Calculate shipping cost based on distance and order value using tiered rates.

    Tiered rates:
    - Orders < $20: $0.50 per mile
    - Orders $20-$100: $0.20 per mile
    - Orders > $100: $0.30 per mile

    Args:
        distance_miles: Distance in miles
        order_value: Order value in dollars

    Returns: Dictionary with shipping_cost, rate_used, and tier
    """
    logging.info(f"TOOL CALL - calculate_shipping_cost: {distance_miles}")
    # Determine tier and rate
    if order_value < 20:
        rate = 0.50
        tier = "Small order (<$20)"
    elif order_value <= 100:
        rate = 0.20
        tier = "Medium order ($20-$100)"
    else:
        rate = 0.30
        tier = "Large order (>$100)"

    # Calculate cost
    shipping_cost = distance_miles * rate

    return {
        "shipping_cost": round(shipping_cost, 2),
        "rate_per_mile": rate,
        "tier": tier,
        "distance_miles": distance_miles,
        "order_value": order_value
    }


# ============================================================================
# Calculator Tool
# ============================================================================

@tool
def calculator(expression: str) -> float:
    """
    Evaluate a mathematical expression safely.

    Args:
        expression: Math expression as string (e.g., "10 * 0.15", "100 + 50 - 20")

    Returns: Result of calculation

    Supports: +, -, *, /, **, (), percentages
    """
    logging.info(f"TOOL CALL - calculator: {expression}")
    try:
        # Simple safety: only allow numbers and basic math operators
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return f"Error: Invalid characters in expression"

        result = eval(expression)
        return round(result, 2)
    except Exception as e:
        return f"Error calculating: {str(e)}"


# ============================================================================
# Tool Lists for Agent
# ============================================================================

# Language tools - for translation chain demo
LANGUAGE_TOOLS = [detect_language, translate_text]

# Shipping tools - for shipping calculator agent demo
SHIPPING_TOOLS = [calculate_distance, calculate_shipping_cost, calculator]

# All tools combined
ALL_TOOLS = LANGUAGE_TOOLS + SHIPPING_TOOLS
