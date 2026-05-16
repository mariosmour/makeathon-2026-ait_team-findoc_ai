import os
from io import BytesIO
from typing import Any, Dict, List, Optional

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from dotenv import load_dotenv

load_dotenv()


def get_document_client() -> DocumentIntelligenceClient:
    endpoint = os.getenv("DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = os.getenv("DOCUMENT_INTELLIGENCE_KEY")

    if not endpoint or not key:
        raise RuntimeError("Missing Document Intelligence endpoint or key in .env")

    return DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )


def _get(obj: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in obj:
            return obj[key]
    return None


def extract_field_value(field: Dict[str, Any]) -> Any:
    """
    Azure fields can have different value types:
    valueString, valueDate, valueCurrency, valueNumber, etc.
    This helper tries to return the cleanest available value.
    """
    if not field:
        return None

    currency = _get(field, "valueCurrency", "value_currency")
    if isinstance(currency, dict):
        amount = _get(currency, "amount")
        code = _get(currency, "currencyCode", "currency_code")
        if amount is not None and code:
            return f"{amount} {code}"
        return currency

    for key in [
        "valueString", "value_string",
        "valueDate", "value_date",
        "valueTime", "value_time",
        "valuePhoneNumber", "value_phone_number",
        "valueNumber", "value_number",
        "valueInteger", "value_integer",
        "valueBoolean", "value_boolean",
        "content"
    ]:
        value = _get(field, key)
        if value is not None:
            return value

    return field.get("content")


def extract_bounding_info(field: Dict[str, Any]) -> Dict[str, Any]:
    regions = _get(field, "boundingRegions", "bounding_regions") or []

    if not regions:
        return {
            "page": None,
            "polygon": None
        }

    first = regions[0]
    return {
        "page": _get(first, "pageNumber", "page_number"),
        "polygon": _get(first, "polygon")
    }


def simplify_field(field: Dict[str, Any]) -> Dict[str, Any]:
    bbox = extract_bounding_info(field)

    return {
        "value": extract_field_value(field),
        "content": field.get("content"),
        "confidence": field.get("confidence"),
        "page": bbox["page"],
        "polygon": bbox["polygon"]
    }


def parse_line_items(fields: Dict[str, Any]) -> List[Dict[str, Any]]:
    items_field = fields.get("Items") or fields.get("InvoiceItems")

    if not items_field:
        return []

    value_array = _get(items_field, "valueArray", "value_array") or []
    line_items = []

    for item in value_array:
        obj = _get(item, "valueObject", "value_object") or {}

        parsed_item = {}
        for key, value in obj.items():
            parsed_item[key] = simplify_field(value)

        line_items.append(parsed_item)

    return line_items


def analyze_invoice(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    client = get_document_client()

    poller = client.begin_analyze_document(
        "prebuilt-invoice",
        body=BytesIO(file_bytes)
    )

    result = poller.result()
    result_dict = result.as_dict()

    documents = result_dict.get("documents", [])

    if not documents:
        return {
            "filename": filename,
            "raw_text": result_dict.get("content", ""),
            "fields": {},
            "line_items": [],
            "raw": result_dict
        }

    doc = documents[0]
    fields = doc.get("fields", {})

    parsed_fields = {}

    for field_name, field_data in fields.items():
        if field_name in ["Items", "InvoiceItems"]:
            continue

        parsed_fields[field_name] = simplify_field(field_data)

    line_items = parse_line_items(fields)

    return {
        "filename": filename,
        "raw_text": result_dict.get("content", ""),
        "fields": parsed_fields,
        "line_items": line_items,
        "raw": result_dict
    }