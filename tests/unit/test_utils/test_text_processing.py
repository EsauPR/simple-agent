"""Tests for text_processing utilities"""
from src.utils.text_processing import (
    normalize_text,
    normalize_brand,
    normalize_model,
    find_similar_brand,
    find_similar_model,
    extract_car_references,
)


class TestNormalizeText:
    """Tests for normalize_text function"""

    def test_normalize_text_lowercase(self):
        """Test lowercase conversion"""
        assert normalize_text("TOYOTA") == "toyota"
        assert normalize_text("Corolla") == "corolla"

    def test_normalize_text_trim_spaces(self):
        """Test trimming spaces"""
        assert normalize_text("  toyota  ") == "toyota"
        assert normalize_text("  corolla  ") == "corolla"

    def test_normalize_text_remove_accents(self):
        """Test accent removal"""
        assert normalize_text("México") == "mexico"
        assert normalize_text("José") == "jose"

    def test_normalize_text_multiple_spaces(self):
        """Test multiple spaces normalization"""
        assert normalize_text("toyota   corolla") == "toyota corolla"
        assert normalize_text("mercedes  benz") == "mercedes benz"

    def test_normalize_text_empty(self):
        """Test empty string"""
        assert normalize_text("") == ""
        assert normalize_text(None) == ""


class TestNormalizeBrand:
    """Tests for normalize_brand function"""

    def test_normalize_brand_known_variants(self):
        """Test known brand variants"""
        assert normalize_brand("vw") == "volkswagen"
        assert normalize_brand("mercedes") == "mercedes benz"
        assert normalize_brand("mercedes-benz") == "mercedes benz"
        assert normalize_brand("chev") == "chevrolet"

    def test_normalize_brand_exact_match(self):
        """Test exact brand match"""
        assert normalize_brand("toyota") == "toyota"
        assert normalize_brand("honda") == "honda"
        assert normalize_brand("bmw") == "bmw"

    def test_normalize_brand_fuzzy_match(self):
        """Test fuzzy matching"""
        # Should match with high similarity
        result = normalize_brand("toyta")  # typo
        assert result is not None

    def test_normalize_brand_case_insensitive(self):
        """Test case insensitive"""
        assert normalize_brand("TOYOTA") == "toyota"
        assert normalize_brand("Toyota") == "toyota"

    def test_normalize_brand_none(self):
        """Test None input"""
        assert normalize_brand(None) is None
        assert normalize_brand("") is None


class TestNormalizeModel:
    """Tests for normalize_model function"""

    def test_normalize_model_basic(self):
        """Test basic model normalization"""
        assert normalize_model("Corolla") == "corolla"
        assert normalize_model("CIVIC") == "civic"

    def test_normalize_model_with_spaces(self):
        """Test model with spaces"""
        assert normalize_model("  Corolla  ") == "corolla"
        assert normalize_model("Mazda 3") == "mazda 3"

    def test_normalize_model_empty(self):
        """Test empty model"""
        assert normalize_model("") == ""
        assert normalize_model(None) == ""


class TestFindSimilarBrand:
    """Tests for find_similar_brand function"""

    def test_find_similar_brand_exact_match(self):
        """Test exact brand match"""
        available = ["Toyota", "Honda", "Nissan"]
        assert find_similar_brand("Toyota", available) == "Toyota"
        assert find_similar_brand("toyota", available) == "Toyota"

    def test_find_similar_brand_fuzzy_match(self):
        """Test fuzzy matching"""
        available = ["Toyota", "Honda", "Nissan", "Volkswagen"]
        result = find_similar_brand("toyta", available)  # typo
        assert result == "Toyota"

    def test_find_similar_brand_no_match(self):
        """Test no match found"""
        available = ["Toyota", "Honda"]
        assert find_similar_brand("Ferrari", available) is None

    def test_find_similar_brand_empty_available(self):
        """Test empty available list"""
        assert find_similar_brand("Toyota", []) is None

    def test_find_similar_brand_none_input(self):
        """Test None input"""
        assert find_similar_brand(None, ["Toyota"]) is None
        assert find_similar_brand("Toyota", None) is None


class TestFindSimilarModel:
    """Tests for find_similar_model function"""

    def test_find_similar_model_exact_match(self):
        """Test exact model match"""
        available = ["Corolla", "Civic", "Sentra"]
        assert find_similar_model("Corolla", available) == "Corolla"
        assert find_similar_model("corolla", available) == "Corolla"

    def test_find_similar_model_fuzzy_match(self):
        """Test fuzzy matching"""
        available = ["Corolla", "Civic", "Sentra"]
        result = find_similar_model("corola", available)  # typo
        assert result == "Corolla"

    def test_find_similar_model_no_match(self):
        """Test no match found"""
        available = ["Corolla", "Civic"]
        assert find_similar_model("Ferrari", available) is None

    def test_find_similar_model_empty_available(self):
        """Test empty available list"""
        assert find_similar_model("Corolla", []) is None

    def test_find_similar_model_none_input(self):
        """Test None input"""
        assert find_similar_model(None, ["Corolla"]) is None
        assert find_similar_model("Corolla", None) is None


class TestExtractCarReferences:
    """Tests for extract_car_references function"""

    def test_extract_car_references_two_words(self):
        """Test extraction with two words"""
        brand, model = extract_car_references("Toyota Corolla")
        assert brand == "toyota"
        assert model == "corolla"

    def test_extract_car_references_three_words(self):
        """Test extraction with three words"""
        brand, model = extract_car_references("Mercedes Benz C200")
        # The function takes first word as brand, second as model
        # So "Mercedes" is brand, "Benz" is model (not "C200")
        assert brand == "mercedes benz"  # normalize_brand converts "mercedes" to "mercedes benz"
        assert model == "benz"  # Second word is "benz"

    def test_extract_car_references_single_word(self):
        """Test extraction with single word"""
        brand, model = extract_car_references("Toyota")
        assert brand is None
        assert model is None

    def test_extract_car_references_empty(self):
        """Test empty input"""
        brand, model = extract_car_references("")
        assert brand is None
        assert model is None

    def test_extract_car_references_none(self):
        """Test None input"""
        brand, model = extract_car_references(None)
        assert brand is None
        assert model is None

    def test_extract_car_references_case_insensitive(self):
        """Test case insensitive extraction"""
        brand, model = extract_car_references("TOYOTA COROLLA")
        assert brand == "toyota"
        assert model == "corolla"
