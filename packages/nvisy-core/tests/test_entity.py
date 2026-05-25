"""Tests for the entity taxonomy."""

from nvisy_core.entity import EntityCategory, EntityKind


def test_every_kind_resolves_to_a_category():
    # The module asserts this at import time too; make it an explicit test.
    for kind in EntityKind:
        assert isinstance(kind.category, EntityCategory)


def test_wire_values_are_snake_case():
    assert EntityKind.PERSON_NAME.value == "person_name"
    assert EntityCategory.PERSONAL_IDENTITY.value == "personal_identity"


def test_kind_category_matches_runtime_examples():
    # Spot-check a few mappings against the runtime's EntityKind::category().
    assert EntityKind.EMAIL_ADDRESS.category == EntityCategory.CONTACT_INFO
    assert EntityKind.IBAN.category == EntityCategory.FINANCIAL
    assert EntityKind.DATE_TIME.category == EntityCategory.PERSONAL_IDENTITY
    assert EntityKind.UNRESOLVED.category == EntityCategory.UNRESOLVED
