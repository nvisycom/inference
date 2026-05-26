"""Mapping between GLiNER's free-text labels and the canonical entity taxonomy.

GLiNER is zero-shot: it takes arbitrary label strings at inference time and
returns the same strings on its spans. This module is the service's own
translation layer between those model-specific strings and
:class:`~nvisy_core.entity.EntityKind`:

- **request:** a requested :class:`EntityKind` -> the GLiNER label(s) to ask for.
- **response:** a GLiNER span's label -> the :class:`EntityKind` to report.

Owning this here is what makes the model swappable without a runtime change.
The default map covers every text-detectable :class:`EntityKind` (see
``DEFAULT_KIND_TO_LABEL`` for what's deliberately omitted); a deployment can
override it (e.g. for BYO weights trained on different labels).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from nvisy_core.entity import EntityKind

# kind -> the GLiNER label string we ask the model for. GLiNER is zero-shot, so
# the label is just a natural-language phrase describing the kind; phrasing
# affects accuracy (GLiNER prefers lowercase, spelled-out descriptions).
#
# Covers every EntityKind that is *text-detectable*. Deliberately omitted:
# visual/biometric kinds (face, fingerprint, voiceprint, retina_scan,
# facial_geometry, handwriting, signature, logo, barcode) — those are not text,
# so a text NER model can't find them; they belong to the OCR/CV path. Also
# omitted: `unresolved` (a fallback, not a request target). A deployment can
# override this map (e.g. for BYO weights trained on different labels).
DEFAULT_KIND_TO_LABEL: dict[EntityKind, str] = {
    # Personal identity
    EntityKind.PERSON_NAME: "person",
    EntityKind.DATE_OF_BIRTH: "date of birth",
    EntityKind.GOVERNMENT_ID: "government id number",
    EntityKind.TAX_ID: "tax id number",
    EntityKind.DRIVERS_LICENSE: "driver's license number",
    EntityKind.PASSPORT_NUMBER: "passport number",
    EntityKind.NATIONAL_INSURANCE_NUMBER: "national insurance number",
    EntityKind.VEHICLE_ID: "vehicle identification number",
    EntityKind.LICENSE_PLATE: "license plate number",
    # Contact information
    EntityKind.EMAIL_ADDRESS: "email",
    EntityKind.PHONE_NUMBER: "phone number",
    EntityKind.ADDRESS: "address",
    EntityKind.POSTAL_CODE: "postal code",
    EntityKind.URL: "url",
    # Demographic
    EntityKind.AGE: "age",
    EntityKind.GENDER: "gender",
    EntityKind.ETHNICITY: "ethnicity",
    EntityKind.RELIGION: "religion",
    EntityKind.NATIONALITY: "nationality",
    EntityKind.CITIZENSHIP: "citizenship",
    EntityKind.LANGUAGE: "language",
    # Financial
    EntityKind.PAYMENT_CARD: "credit card number",
    EntityKind.CARD_SECURITY_CODE: "card security code",
    EntityKind.CARD_EXPIRY: "card expiration date",
    EntityKind.BANK_ACCOUNT: "bank account number",
    EntityKind.BANK_ROUTING: "bank routing number",
    EntityKind.IBAN: "iban",
    EntityKind.SWIFT_CODE: "swift code",
    EntityKind.CRYPTO_ADDRESS: "cryptocurrency address",
    EntityKind.AMOUNT: "monetary amount",
    # Health
    EntityKind.MEDICAL_ID: "medical record number",
    EntityKind.INSURANCE_ID: "insurance id number",
    EntityKind.PRESCRIPTION_ID: "prescription number",
    EntityKind.DIAGNOSIS: "medical diagnosis",
    EntityKind.MEDICATION: "medication",
    # Credentials (GLiNER is weaker here than pattern matching, but text-visible)
    EntityKind.PASSWORD: "password",
    EntityKind.API_KEY: "api key",
    EntityKind.AUTH_TOKEN: "authentication token",
    EntityKind.PRIVATE_KEY: "private key",
    # Network and device identifiers
    EntityKind.IP_ADDRESS: "ip address",
    EntityKind.MAC_ADDRESS: "mac address",
    EntityKind.DEVICE_ID: "device id",
    EntityKind.USERNAME: "username",
    # Location
    EntityKind.COORDINATES: "geographic coordinates",
    EntityKind.GEOLOCATION_METADATA: "location",
    # Organizational
    EntityKind.ORGANIZATION_NAME: "organization",
    EntityKind.DEPARTMENT_NAME: "department",
    EntityKind.FACILITY_NAME: "facility",
    EntityKind.CASE_NUMBER: "case number",
    EntityKind.INTERNAL_ID: "internal id",
    # Temporal
    EntityKind.DATE_TIME: "date",
    # General-purpose
    EntityKind.EVENT: "event",
    EntityKind.OCCUPATION: "occupation",
    EntityKind.PRODUCT: "product",
    EntityKind.QUANTITY: "quantity",
}


class LabelMap:
    """Bidirectional map between GLiNER labels and entity kinds.

    The mapping must be injective (each label maps to exactly one kind) so the
    reverse lookup used by :meth:`classify` is unambiguous; this is enforced at
    construction.
    """

    def __init__(self, kind_to_label: Mapping[EntityKind, str] | None = None) -> None:
        self._kind_to_label: dict[EntityKind, str] = dict(kind_to_label or DEFAULT_KIND_TO_LABEL)
        reverse: dict[str, EntityKind] = {}
        for kind, label in self._kind_to_label.items():
            if label in reverse:
                raise ValueError(
                    f"label {label!r} maps to both {reverse[label]} and {kind}; "
                    "the label map must be injective"
                )
            reverse[label] = kind
        self._label_to_kind = reverse

    def labels_for(self, kinds: Iterable[EntityKind]) -> list[str]:
        """The GLiNER labels to request for ``kinds``, de-duplicated, order-stable.

        Kinds with no mapping (e.g. visual/biometric) are skipped.
        """
        labels = (self._kind_to_label[k] for k in kinds if k in self._kind_to_label)
        return list(dict.fromkeys(labels))

    def classify(self, label: str) -> EntityKind | None:
        """The kind for a GLiNER span label, or ``None`` if unmapped (dropped)."""
        return self._label_to_kind.get(label)


DEFAULT_LABEL_MAP = LabelMap()
