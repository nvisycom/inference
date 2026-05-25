"""Entity taxonomy: the canonical categories and kinds the wire speaks.

Inference services classify model output into this taxonomy, so swapping the
underlying model (or bringing your own) never requires a runtime change — the
service maps its model's labels to an :class:`EntityKind`, and the runtime
consumes those kinds directly.

This mirrors the Rust runtime's ``EntityCategory`` / ``EntityKind`` enums
(``nvisy-ontology``), which are the ultimate source of truth. Wire values are
``snake_case`` to match the runtime's serde ``rename_all = "snake_case"``.

Every :class:`EntityKind` belongs to exactly one :class:`EntityCategory`
(``EntityKind.category``), so the wire carries only the kind — the category is
derivable and can never disagree with it.
"""

from __future__ import annotations

from enum import StrEnum


class EntityCategory(StrEnum):
    """Broad bucket an entity belongs to."""

    PERSONAL_IDENTITY = "personal_identity"
    CONTACT_INFO = "contact_info"
    DEMOGRAPHIC = "demographic"
    FINANCIAL = "financial"
    HEALTH = "health"
    BIOMETRIC = "biometric"
    CREDENTIALS = "credentials"
    NETWORK_IDENTIFIER = "network_identifier"
    LOCATION = "location"
    VISUAL = "visual"
    ORGANIZATIONAL = "organizational"
    GENERAL_PURPOSE = "general_purpose"
    UNRESOLVED = "unresolved"


class EntityKind(StrEnum):
    """Specific kind of entity. Each kind maps to one :class:`EntityCategory`."""

    # Personal identity
    PERSON_NAME = "person_name"
    DATE_OF_BIRTH = "date_of_birth"
    GOVERNMENT_ID = "government_id"
    TAX_ID = "tax_id"
    DRIVERS_LICENSE = "drivers_license"
    PASSPORT_NUMBER = "passport_number"
    NATIONAL_INSURANCE_NUMBER = "national_insurance_number"
    VEHICLE_ID = "vehicle_id"
    LICENSE_PLATE = "license_plate"

    # Contact information
    EMAIL_ADDRESS = "email_address"
    PHONE_NUMBER = "phone_number"
    ADDRESS = "address"
    POSTAL_CODE = "postal_code"
    URL = "url"

    # Demographic
    AGE = "age"
    GENDER = "gender"
    ETHNICITY = "ethnicity"
    RELIGION = "religion"
    NATIONALITY = "nationality"
    CITIZENSHIP = "citizenship"
    LANGUAGE = "language"

    # Financial
    PAYMENT_CARD = "payment_card"
    CARD_SECURITY_CODE = "card_security_code"
    CARD_EXPIRY = "card_expiry"
    BANK_ACCOUNT = "bank_account"
    BANK_ROUTING = "bank_routing"
    IBAN = "iban"
    SWIFT_CODE = "swift_code"
    CRYPTO_ADDRESS = "crypto_address"
    AMOUNT = "amount"

    # Health
    MEDICAL_ID = "medical_id"
    INSURANCE_ID = "insurance_id"
    PRESCRIPTION_ID = "prescription_id"
    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"

    # Biometric
    FINGERPRINT = "fingerprint"
    VOICEPRINT = "voiceprint"
    RETINA_SCAN = "retina_scan"
    FACIAL_GEOMETRY = "facial_geometry"

    # Credentials
    PASSWORD = "password"
    API_KEY = "api_key"
    AUTH_TOKEN = "auth_token"
    PRIVATE_KEY = "private_key"

    # Network and device identifiers
    IP_ADDRESS = "ip_address"
    MAC_ADDRESS = "mac_address"
    DEVICE_ID = "device_id"
    USERNAME = "username"

    # Location
    COORDINATES = "coordinates"
    GEOLOCATION_METADATA = "geolocation_metadata"

    # Visual
    FACE = "face"
    HANDWRITING = "handwriting"
    SIGNATURE = "signature"
    LOGO = "logo"
    BARCODE = "barcode"

    # Organizational
    ORGANIZATION_NAME = "organization_name"
    DEPARTMENT_NAME = "department_name"
    FACILITY_NAME = "facility_name"
    CASE_NUMBER = "case_number"
    INTERNAL_ID = "internal_id"

    # Temporal (classified under personal identity, mirroring the runtime)
    DATE_TIME = "date_time"

    # General-purpose
    EVENT = "event"
    OCCUPATION = "occupation"
    PRODUCT = "product"
    QUANTITY = "quantity"

    # Fallback
    UNRESOLVED = "unresolved"

    @property
    def category(self) -> EntityCategory:
        """The category this kind belongs to (mirrors ``EntityKind::category``)."""
        return _KIND_TO_CATEGORY[self]


_C = EntityCategory
_K = EntityKind

# Single source of truth for the kind -> category mapping. Mirrors the runtime's
# EntityKind::category() match arms.
_KIND_TO_CATEGORY: dict[EntityKind, EntityCategory] = {
    _K.PERSON_NAME: _C.PERSONAL_IDENTITY,
    _K.DATE_OF_BIRTH: _C.PERSONAL_IDENTITY,
    _K.GOVERNMENT_ID: _C.PERSONAL_IDENTITY,
    _K.TAX_ID: _C.PERSONAL_IDENTITY,
    _K.DRIVERS_LICENSE: _C.PERSONAL_IDENTITY,
    _K.PASSPORT_NUMBER: _C.PERSONAL_IDENTITY,
    _K.NATIONAL_INSURANCE_NUMBER: _C.PERSONAL_IDENTITY,
    _K.VEHICLE_ID: _C.PERSONAL_IDENTITY,
    _K.LICENSE_PLATE: _C.PERSONAL_IDENTITY,
    _K.EMAIL_ADDRESS: _C.CONTACT_INFO,
    _K.PHONE_NUMBER: _C.CONTACT_INFO,
    _K.ADDRESS: _C.CONTACT_INFO,
    _K.POSTAL_CODE: _C.CONTACT_INFO,
    _K.URL: _C.CONTACT_INFO,
    _K.AGE: _C.DEMOGRAPHIC,
    _K.GENDER: _C.DEMOGRAPHIC,
    _K.ETHNICITY: _C.DEMOGRAPHIC,
    _K.RELIGION: _C.DEMOGRAPHIC,
    _K.NATIONALITY: _C.DEMOGRAPHIC,
    _K.CITIZENSHIP: _C.DEMOGRAPHIC,
    _K.LANGUAGE: _C.DEMOGRAPHIC,
    _K.PAYMENT_CARD: _C.FINANCIAL,
    _K.CARD_SECURITY_CODE: _C.FINANCIAL,
    _K.CARD_EXPIRY: _C.FINANCIAL,
    _K.BANK_ACCOUNT: _C.FINANCIAL,
    _K.BANK_ROUTING: _C.FINANCIAL,
    _K.IBAN: _C.FINANCIAL,
    _K.SWIFT_CODE: _C.FINANCIAL,
    _K.CRYPTO_ADDRESS: _C.FINANCIAL,
    _K.AMOUNT: _C.FINANCIAL,
    _K.MEDICAL_ID: _C.HEALTH,
    _K.INSURANCE_ID: _C.HEALTH,
    _K.PRESCRIPTION_ID: _C.HEALTH,
    _K.DIAGNOSIS: _C.HEALTH,
    _K.MEDICATION: _C.HEALTH,
    _K.FINGERPRINT: _C.BIOMETRIC,
    _K.VOICEPRINT: _C.BIOMETRIC,
    _K.RETINA_SCAN: _C.BIOMETRIC,
    _K.FACIAL_GEOMETRY: _C.BIOMETRIC,
    _K.PASSWORD: _C.CREDENTIALS,
    _K.API_KEY: _C.CREDENTIALS,
    _K.AUTH_TOKEN: _C.CREDENTIALS,
    _K.PRIVATE_KEY: _C.CREDENTIALS,
    _K.IP_ADDRESS: _C.NETWORK_IDENTIFIER,
    _K.MAC_ADDRESS: _C.NETWORK_IDENTIFIER,
    _K.DEVICE_ID: _C.NETWORK_IDENTIFIER,
    _K.USERNAME: _C.NETWORK_IDENTIFIER,
    _K.COORDINATES: _C.LOCATION,
    _K.GEOLOCATION_METADATA: _C.LOCATION,
    _K.FACE: _C.VISUAL,
    _K.HANDWRITING: _C.VISUAL,
    _K.SIGNATURE: _C.VISUAL,
    _K.LOGO: _C.VISUAL,
    _K.BARCODE: _C.VISUAL,
    _K.ORGANIZATION_NAME: _C.ORGANIZATIONAL,
    _K.DEPARTMENT_NAME: _C.ORGANIZATIONAL,
    _K.FACILITY_NAME: _C.ORGANIZATIONAL,
    _K.CASE_NUMBER: _C.ORGANIZATIONAL,
    _K.INTERNAL_ID: _C.ORGANIZATIONAL,
    _K.DATE_TIME: _C.PERSONAL_IDENTITY,
    _K.EVENT: _C.GENERAL_PURPOSE,
    _K.OCCUPATION: _C.GENERAL_PURPOSE,
    _K.PRODUCT: _C.GENERAL_PURPOSE,
    _K.QUANTITY: _C.GENERAL_PURPOSE,
    _K.UNRESOLVED: _C.UNRESOLVED,
}

# Fail at import time if a kind is missing from the mapping (drift guard).
assert set(_KIND_TO_CATEGORY) == set(EntityKind), "every EntityKind needs a category"
