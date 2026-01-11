"""Tests for the Nutrition domain module."""

import pytest
from pydantic import ValidationError


class TestMacrosValidation:
    """Tests for Macros model validation."""

    def test_valid_macros(self) -> None:
        """Test that valid macros with all fields works."""
        from swealog.domains import Macros

        m = Macros(protein=30.0, carbs=50.0, fat=15.0)
        assert m.protein == 30.0
        assert m.carbs == 50.0
        assert m.fat == 15.0

    def test_protein_boundary_zero_succeeds(self) -> None:
        """Test that protein exactly 0.0 succeeds."""
        from swealog.domains import Macros

        m = Macros(protein=0.0)
        assert m.protein == 0.0

    def test_carbs_boundary_zero_succeeds(self) -> None:
        """Test that carbs exactly 0.0 succeeds."""
        from swealog.domains import Macros

        m = Macros(carbs=0.0)
        assert m.carbs == 0.0

    def test_fat_boundary_zero_succeeds(self) -> None:
        """Test that fat exactly 0.0 succeeds."""
        from swealog.domains import Macros

        m = Macros(fat=0.0)
        assert m.fat == 0.0

    def test_protein_negative_raises(self) -> None:
        """Test that negative protein raises ValidationError."""
        from swealog.domains import Macros

        with pytest.raises(ValidationError) as exc_info:
            Macros(protein=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_carbs_negative_raises(self) -> None:
        """Test that negative carbs raises ValidationError."""
        from swealog.domains import Macros

        with pytest.raises(ValidationError) as exc_info:
            Macros(carbs=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_fat_negative_raises(self) -> None:
        """Test that negative fat raises ValidationError."""
        from swealog.domains import Macros

        with pytest.raises(ValidationError) as exc_info:
            Macros(fat=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_all_fields_optional(self) -> None:
        """Test that all fields are optional."""
        from swealog.domains import Macros

        m = Macros()
        assert m.protein is None
        assert m.carbs is None
        assert m.fat is None


class TestFoodItemModel:
    """Tests for FoodItem model."""

    def test_food_name_required(self) -> None:
        """Test that food name is required."""
        from swealog.domains import FoodItem

        f = FoodItem(name="chicken salad")
        assert f.name == "chicken salad"

    def test_food_missing_name_raises(self) -> None:
        """Test that missing name raises ValidationError."""
        from swealog.domains import FoodItem

        with pytest.raises(ValidationError):
            FoodItem()  # type: ignore[call-arg]

    def test_food_empty_name_raises(self) -> None:
        """Test that empty name raises ValidationError."""
        from swealog.domains import FoodItem

        with pytest.raises(ValidationError) as exc_info:
            FoodItem(name="")
        assert "at least 1" in str(exc_info.value).lower()

    def test_food_valid_with_all_fields(self) -> None:
        """Test FoodItem with all fields populated."""
        from swealog.domains import FoodItem, Macros

        f = FoodItem(
            name="protein shake",
            quantity="1 scoop",
            calories=120.0,
            macros=Macros(protein=25.0, carbs=3.0, fat=1.0),
            notes="post-workout",
        )
        assert f.name == "protein shake"
        assert f.quantity == "1 scoop"
        assert f.calories == 120.0
        assert f.macros is not None
        assert f.macros.protein == 25.0
        assert f.notes == "post-workout"

    def test_calories_optional(self) -> None:
        """Test that calories field is optional."""
        from swealog.domains import FoodItem

        f = FoodItem(name="apple")
        assert f.calories is None

    def test_calories_boundary_zero_succeeds(self) -> None:
        """Test that calories exactly 0.0 succeeds."""
        from swealog.domains import FoodItem

        f = FoodItem(name="water", calories=0.0)
        assert f.calories == 0.0

    def test_calories_negative_raises(self) -> None:
        """Test that negative calories raises ValidationError."""
        from swealog.domains import FoodItem

        with pytest.raises(ValidationError) as exc_info:
            FoodItem(name="food", calories=-50.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_macros_optional(self) -> None:
        """Test that macros field is optional."""
        from swealog.domains import FoodItem

        f = FoodItem(name="bread")
        assert f.macros is None

    def test_quantity_optional(self) -> None:
        """Test that quantity field is optional."""
        from swealog.domains import FoodItem

        f = FoodItem(name="eggs")
        assert f.quantity is None

    def test_notes_optional(self) -> None:
        """Test that notes field is optional."""
        from swealog.domains import FoodItem

        f = FoodItem(name="rice")
        assert f.notes is None


class TestNutritionEntryModel:
    """Tests for NutritionEntry log schema."""

    def test_food_items_list_default_empty(self) -> None:
        """Test that food_items list defaults to empty."""
        from swealog.domains import NutritionEntry

        entry = NutritionEntry()
        assert entry.food_items == []

    def test_valid_entry_with_food_items(self) -> None:
        """Test creating a valid entry with food items."""
        from swealog.domains import FoodItem, Macros, NutritionEntry

        food_items = [
            FoodItem(name="chicken salad", calories=350.0),
            FoodItem(
                name="protein shake",
                calories=120.0,
                macros=Macros(protein=30.0),
            ),
        ]
        entry = NutritionEntry(
            meal_type="lunch",
            food_items=food_items,
            total_calories=470.0,
            notes="Post-workout meal",
            time="12:30",
        )
        assert len(entry.food_items) == 2
        assert entry.food_items[0].name == "chicken salad"
        assert entry.food_items[1].name == "protein shake"
        assert entry.meal_type == "lunch"
        assert entry.total_calories == 470.0

    def test_total_calories_boundary_zero_succeeds(self) -> None:
        """Test that total_calories exactly 0.0 succeeds."""
        from swealog.domains import NutritionEntry

        entry = NutritionEntry(total_calories=0.0)
        assert entry.total_calories == 0.0

    def test_total_calories_negative_raises(self) -> None:
        """Test that negative total_calories raises ValidationError."""
        from swealog.domains import NutritionEntry

        with pytest.raises(ValidationError) as exc_info:
            NutritionEntry(total_calories=-100.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_hunger_level_range(self) -> None:
        """Test that hunger_level within 1-10 is valid."""
        from swealog.domains import NutritionEntry

        entry = NutritionEntry(hunger_level=7)
        assert entry.hunger_level == 7

    def test_hunger_level_boundary_one_succeeds(self) -> None:
        """Test that hunger_level exactly 1 succeeds."""
        from swealog.domains import NutritionEntry

        entry = NutritionEntry(hunger_level=1)
        assert entry.hunger_level == 1

    def test_hunger_level_boundary_ten_succeeds(self) -> None:
        """Test that hunger_level exactly 10 succeeds."""
        from swealog.domains import NutritionEntry

        entry = NutritionEntry(hunger_level=10)
        assert entry.hunger_level == 10

    def test_hunger_level_below_one_raises(self) -> None:
        """Test that hunger_level below 1 raises ValidationError."""
        from swealog.domains import NutritionEntry

        with pytest.raises(ValidationError) as exc_info:
            NutritionEntry(hunger_level=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_hunger_level_above_ten_raises(self) -> None:
        """Test that hunger_level above 10 raises ValidationError."""
        from swealog.domains import NutritionEntry

        with pytest.raises(ValidationError) as exc_info:
            NutritionEntry(hunger_level=11)
        assert "less than or equal to 10" in str(exc_info.value)

    def test_satisfaction_level_range(self) -> None:
        """Test that satisfaction_level within 1-10 is valid."""
        from swealog.domains import NutritionEntry

        entry = NutritionEntry(satisfaction_level=8)
        assert entry.satisfaction_level == 8

    def test_satisfaction_level_boundary_one_succeeds(self) -> None:
        """Test that satisfaction_level exactly 1 succeeds."""
        from swealog.domains import NutritionEntry

        entry = NutritionEntry(satisfaction_level=1)
        assert entry.satisfaction_level == 1

    def test_satisfaction_level_boundary_ten_succeeds(self) -> None:
        """Test that satisfaction_level exactly 10 succeeds."""
        from swealog.domains import NutritionEntry

        entry = NutritionEntry(satisfaction_level=10)
        assert entry.satisfaction_level == 10

    def test_satisfaction_level_below_one_raises(self) -> None:
        """Test that satisfaction_level below 1 raises ValidationError."""
        from swealog.domains import NutritionEntry

        with pytest.raises(ValidationError) as exc_info:
            NutritionEntry(satisfaction_level=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_satisfaction_level_above_ten_raises(self) -> None:
        """Test that satisfaction_level above 10 raises ValidationError."""
        from swealog.domains import NutritionEntry

        with pytest.raises(ValidationError) as exc_info:
            NutritionEntry(satisfaction_level=11)
        assert "less than or equal to 10" in str(exc_info.value)

    def test_meal_type_optional(self) -> None:
        """Test that meal_type is optional."""
        from swealog.domains import NutritionEntry

        entry = NutritionEntry()
        assert entry.meal_type is None

    def test_meal_type_accepts_custom_values(self) -> None:
        """Test that meal_type accepts custom values like pre-workout."""
        from swealog.domains import NutritionEntry

        entry = NutritionEntry(meal_type="pre-workout")
        assert entry.meal_type == "pre-workout"


class TestNutritionDomainModule:
    """Tests for Nutrition DomainModule configuration."""

    def test_instantiation(self) -> None:
        """Test that Nutrition domain can be instantiated."""
        from swealog.domains import Nutrition, nutrition

        assert nutrition is not None
        assert isinstance(nutrition, Nutrition)

    def test_name_defaults_to_class_name(self) -> None:
        """Test that domain name defaults to class name."""
        from swealog.domains import nutrition

        assert nutrition.name == "Nutrition"

    def test_description_non_empty(self) -> None:
        """Test that description is non-empty."""
        from swealog.domains import nutrition

        assert nutrition.description
        assert len(nutrition.description) > 0

    def test_vocabulary_contains_calorie_abbreviations(self) -> None:
        """Test that vocabulary contains calorie abbreviations."""
        from swealog.domains import nutrition

        assert nutrition.vocabulary["cal"] == "calories"
        assert nutrition.vocabulary["kcal"] == "calories"
        assert nutrition.vocabulary["cals"] == "calories"

    def test_vocabulary_contains_macro_abbreviations(self) -> None:
        """Test that vocabulary contains macro abbreviations."""
        from swealog.domains import nutrition

        assert nutrition.vocabulary["p"] == "protein"
        assert nutrition.vocabulary["c"] == "carbs"
        assert nutrition.vocabulary["f"] == "fat"
        assert nutrition.vocabulary["carb"] == "carbs"

    def test_vocabulary_contains_korean_meal_terms(self) -> None:
        """Test that vocabulary contains Korean meal names."""
        from swealog.domains import nutrition

        assert nutrition.vocabulary["아침"] == "breakfast"
        assert nutrition.vocabulary["점심"] == "lunch"
        assert nutrition.vocabulary["저녁"] == "dinner"
        assert nutrition.vocabulary["간식"] == "snack"

    def test_vocabulary_contains_korean_nutrition_terms(self) -> None:
        """Test that vocabulary contains Korean nutrition terms."""
        from swealog.domains import nutrition

        assert nutrition.vocabulary["단백질"] == "protein"
        assert nutrition.vocabulary["탄수화물"] == "carbs"
        assert nutrition.vocabulary["지방"] == "fat"
        assert nutrition.vocabulary["칼로리"] == "calories"

    def test_vocabulary_contains_unit_normalizations(self) -> None:
        """Test that vocabulary contains unit normalizations."""
        from swealog.domains import nutrition

        assert nutrition.vocabulary["g"] == "grams"
        assert nutrition.vocabulary["oz"] == "ounces"
        assert nutrition.vocabulary["ml"] == "milliliters"
        assert nutrition.vocabulary["tbsp"] == "tablespoons"
        assert nutrition.vocabulary["tsp"] == "teaspoons"

    def test_expertise_non_empty(self) -> None:
        """Test that expertise is non-empty."""
        from swealog.domains import nutrition

        assert nutrition.expertise
        assert len(nutrition.expertise) > 0
        assert "calories" in nutrition.expertise.lower()

    def test_response_evaluation_rules_populated(self) -> None:
        """Test that response_evaluation_rules is populated."""
        from swealog.domains import nutrition

        assert nutrition.response_evaluation_rules
        assert len(nutrition.response_evaluation_rules) > 0
        assert any("calorie restriction" in rule.lower() for rule in nutrition.response_evaluation_rules)

    def test_context_management_guidance_populated(self) -> None:
        """Test that context_management_guidance is populated."""
        from swealog.domains import nutrition

        assert nutrition.context_management_guidance
        assert len(nutrition.context_management_guidance) > 0
        assert "calories" in nutrition.context_management_guidance.lower()


class TestNutritionSingleton:
    """Tests for nutrition singleton instance."""

    def test_singleton_importable(self) -> None:
        """Test that nutrition singleton is importable from swealog.domains."""
        from swealog.domains import nutrition as imported_nutrition

        assert imported_nutrition is not None

    def test_singleton_is_nutrition_instance(self) -> None:
        """Test that singleton is a Nutrition instance."""
        from swealog.domains import Nutrition, nutrition

        assert isinstance(nutrition, Nutrition)


class TestNutritionIntegration:
    """Integration tests with other domains."""

    def test_nutrition_and_general_fitness_coexist(self) -> None:
        """Test that Nutrition and GeneralFitness domains can coexist."""
        from swealog.domains import GeneralFitness, Nutrition, general_fitness, nutrition

        assert nutrition is not None
        assert general_fitness is not None
        assert isinstance(nutrition, Nutrition)
        assert isinstance(general_fitness, GeneralFitness)
        assert nutrition.name != general_fitness.name

    def test_nutrition_and_strength_coexist(self) -> None:
        """Test that Nutrition and Strength domains can coexist."""
        from swealog.domains import Nutrition, Strength, nutrition, strength

        assert nutrition is not None
        assert strength is not None
        assert isinstance(nutrition, Nutrition)
        assert isinstance(strength, Strength)
        assert nutrition.name != strength.name

    def test_all_three_domains_coexist(self) -> None:
        """Test that all three domains can coexist."""
        from swealog.domains import (
            GeneralFitness,
            Nutrition,
            Strength,
            general_fitness,
            nutrition,
            strength,
        )

        assert nutrition is not None
        assert strength is not None
        assert general_fitness is not None
        assert isinstance(nutrition, Nutrition)
        assert isinstance(strength, Strength)
        assert isinstance(general_fitness, GeneralFitness)
        # All have unique names
        names = {nutrition.name, strength.name, general_fitness.name}
        assert len(names) == 3

    def test_imports_from_swealog_domains(self) -> None:
        """Test that all exports are importable from swealog.domains."""
        from swealog.domains import (
            FoodItem,
            Macros,
            Nutrition,
            NutritionEntry,
            nutrition,
        )

        assert Nutrition is not None
        assert NutritionEntry is not None
        assert FoodItem is not None
        assert Macros is not None
        assert nutrition is not None

    def test_log_schema_is_nutrition_entry(self) -> None:
        """Test that Nutrition domain's log_schema is NutritionEntry."""
        from swealog.domains import NutritionEntry, nutrition

        assert nutrition.log_schema is NutritionEntry


class TestNutritionEntryDateTimeFields:
    """Tests for NutritionEntry date and time fields (AC#3)."""

    def test_date_field_accepts_iso_format(self) -> None:
        """Test that date field accepts ISO date string."""
        from swealog.domains import NutritionEntry

        entry = NutritionEntry(date="2025-01-12")
        assert entry.date == "2025-01-12"

    def test_time_field_accepts_various_formats(self) -> None:
        """Test that time field accepts various time format strings."""
        from swealog.domains import NutritionEntry

        # Standard time format
        entry1 = NutritionEntry(time="12:30")
        assert entry1.time == "12:30"

        # Informal time format
        entry2 = NutritionEntry(time="around noon")
        assert entry2.time == "around noon"

        # AM/PM format
        entry3 = NutritionEntry(time="8am")
        assert entry3.time == "8am"

    def test_date_field_optional(self) -> None:
        """Test that date field is optional."""
        from swealog.domains import NutritionEntry

        entry = NutritionEntry()
        assert entry.date is None

    def test_time_field_optional(self) -> None:
        """Test that time field is optional."""
        from swealog.domains import NutritionEntry

        entry = NutritionEntry()
        assert entry.time is None


class TestVocabularyCompleteness:
    """Tests for vocabulary completeness and accuracy."""

    def test_vocabulary_minimum_size(self) -> None:
        """Test that vocabulary has minimum expected number of terms."""
        from swealog.domains import nutrition

        # Should have at least 50 vocabulary entries (we defined ~61)
        assert len(nutrition.vocabulary) >= 50

    def test_all_calorie_abbreviations_present(self) -> None:
        """Test all documented calorie abbreviations are in vocabulary."""
        from swealog.domains import nutrition

        calorie_abbrevs = ["cal", "cals", "kcal", "kcals", "calorie"]
        for abbrev in calorie_abbrevs:
            assert abbrev in nutrition.vocabulary
            assert nutrition.vocabulary[abbrev] == "calories"

    def test_all_korean_meal_terms_present(self) -> None:
        """Test all documented Korean meal terms are in vocabulary."""
        from swealog.domains import nutrition

        korean_meals = {
            "아침": "breakfast",
            "아침식사": "breakfast",
            "점심": "lunch",
            "점심식사": "lunch",
            "저녁": "dinner",
            "저녁식사": "dinner",
            "간식": "snack",
            "야식": "late-night snack",
            "브런치": "brunch",
        }
        for korean, english in korean_meals.items():
            assert korean in nutrition.vocabulary, f"Missing Korean term: {korean}"
            assert nutrition.vocabulary[korean] == english
