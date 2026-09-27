"""Five-country hackathon configuration, not a claim about current BRICS membership."""
from app.models.provenance import CountryCode

COUNTRIES = [
    {"id": "IN", "iso3": "IND", "name": "India", "region_label": "State / Union Territory", "detailed": True},
    {"id": "BR", "iso3": "BRA", "name": "Brazil", "region_label": "State", "detailed": False},
    {"id": "RU", "iso3": "RUS", "name": "Russia", "region_label": "Federal subject", "detailed": False},
    {"id": "CN", "iso3": "CHN", "name": "China", "region_label": "Province / Municipality", "detailed": False},
    {"id": "ZA", "iso3": "ZAF", "name": "South Africa", "region_label": "Province", "detailed": False},
]
COUNTRY_BY_ID = {country["id"]: country for country in COUNTRIES}
ISO3_TO_ID = {country["iso3"]: country["id"] for country in COUNTRIES}


def country_name(code: CountryCode) -> str:
    return COUNTRY_BY_ID[code]["name"]
