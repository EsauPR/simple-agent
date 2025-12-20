import re
from typing import Optional, Tuple
from thefuzz import fuzz, process


# Mapeo de variaciones comunes de marcas
BRAND_VARIANTS = {
    "vw": "volkswagen",
    "volkswagen": "volkswagen",
    "mercedes": "mercedes benz",
    "mercedes benz": "mercedes benz",
    "mercedes-benz": "mercedes benz",
    "bmw": "bmw",
    "toyota": "toyota",
    "honda": "honda",
    "nissan": "nissan",
    "ford": "ford",
    "chevrolet": "chevrolet",
    "chev": "chevrolet",
    "mazda": "mazda",
    "kia": "kia",
    "volvo": "volvo",
    "audi": "audi",
    "jeep": "jeep",
    "land rover": "land rover",
    "landrover": "land rover",
    "dodge": "dodge",
    "renault": "renault",
    "fiat": "fiat",
    "mini": "mini",
    "infiniti": "infiniti",
    "lincoln": "lincoln",
    "mg": "mg",
    "suzuki": "suzuki",
    "peugeot": "peugeot",
    "seat": "seat",
    "jac": "jac",
}


def normalize_text(text: str) -> str:
    """Normaliza texto: lowercase, sin acentos, sin espacios extra"""
    if not text:
        return ""

    # Convertir a lowercase
    text = text.lower().strip()

    # Remover acentos básicos (puede expandirse)
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ñ": "n"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remover espacios extra
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def normalize_brand(brand: str) -> Optional[str]:
    """Normaliza y corrige nombre de marca"""
    if not brand:
        return None

    normalized = normalize_text(brand)

    # Buscar en variantes conocidas
    if normalized in BRAND_VARIANTS:
        return BRAND_VARIANTS[normalized]

    # Fuzzy matching con variantes conocidas
    brands_list = list(BRAND_VARIANTS.keys())
    match = process.extractOne(normalized, brands_list, scorer=fuzz.ratio)

    if match and match[1] >= 70:  # Threshold de 70%
        return BRAND_VARIANTS[match[0]]

    return normalized


def normalize_model(model: str) -> str:
    """Normaliza nombre de modelo"""
    if not model:
        return ""
    return normalize_text(model)


def find_similar_brand(brand: str, available_brands: list[str], threshold: int = 70) -> Optional[str]:
    """Encuentra marca similar usando fuzzy matching"""
    if not brand or not available_brands:
        return None

    normalized_brand = normalize_brand(brand)
    if not normalized_brand:
        return None

    # Buscar coincidencia exacta primero
    for available in available_brands:
        if normalize_brand(available) == normalized_brand:
            return available

    # Fuzzy matching
    match = process.extractOne(normalized_brand, available_brands, scorer=fuzz.ratio)

    if match and match[1] >= threshold:
        return match[0]

    return None


def find_similar_model(model: str, available_models: list[str], threshold: int = 70) -> Optional[str]:
    """Encuentra modelo similar usando fuzzy matching"""
    if not model or not available_models:
        return None

    normalized_model = normalize_model(model)

    # Buscar coincidencia exacta primero
    for available in available_models:
        if normalize_model(available) == normalized_model:
            return available

    # Fuzzy matching
    match = process.extractOne(normalized_model, available_models, scorer=fuzz.ratio)

    if match and match[1] >= threshold:
        return match[0]

    return None


def extract_car_references(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extrae marca y modelo de un texto"""
    if not text:
        return None, None

    normalized = normalize_text(text)

    # Buscar patrones comunes
    # "Toyota Corolla", "BMW X5", etc.
    words = normalized.split()

    # Si hay 2+ palabras, las primeras pueden ser marca y modelo
    if len(words) >= 2:
        potential_brand = " ".join(words[:1])
        potential_model = " ".join(words[1:2])

        brand = normalize_brand(potential_brand)
        model = normalize_model(potential_model)

        return brand, model

    return None, None
