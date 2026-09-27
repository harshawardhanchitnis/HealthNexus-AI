"""MoHFW HDI 2022–23 national summary published by PIB, release 2053070.

This is a parser for a dated publication, not an HMIS API or a facility registry.
Only the two quantitative paragraphs are cached, without images or article prose.
"""
import re
from html.parser import HTMLParser

import httpx

from app.data_ingestion.base import RawSnapshot, raw_snapshot
from app.models.provenance import Observation, Provenance, PublicDataset

URL = "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2053070"


class Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.paragraphs = [], []
        self.inside = False

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.inside, self.parts = True, []

    def handle_endtag(self, tag):
        if tag == "p" and self.inside:
            self.paragraphs.append(" ".join(" ".join(self.parts).split()))
            self.inside = False

    def handle_data(self, data):
        if self.inside:
            self.parts.append(data)


FIELDS = {
    "sc_count": (r"Sub-Centres \(SCs\)", "Sub-centres"),
    "phc_count": (r"Primary Health Centres \(PHCs\)", "Primary health centres"),
    "chc_count": (r"Community Health Centres \(CHCs\)", "Community health centres"),
    "sdh_count": (r"Sub-Divisional/District Hospitals \(SDHs\)", "Sub-divisional hospitals (source wording: SDHs)"),
    "dh_count": (r"District Hospitals \(DHs\)", "District hospitals"),
    "medical_college_count": (r"Medical Colleges \(MCs\)", "Medical colleges"),
    "sc_health_workers": (r"Health Worker \(Male \+ Female\) at SCs", "Health workers at sub-centres"),
    "phc_doctors": (r"Doctors/Medical Officers at PHCs", "Doctors / medical officers at PHCs"),
    "chc_doctors": (r"Specialists & Medical Officers at CHCs", "Specialists / medical officers at CHCs"),
    "sdh_dh_doctors": (r"Doctors and Specialists at SDHs and DHs", "Doctors / specialists at SDHs and DHs"),
    "phc_nurses": (r"Staff Nurses at PHCs", "Staff nurses at PHCs"),
    "chc_nurses": (r"Nursing Staff at CHCs", "Nursing staff at CHCs"),
    "sdh_dh_paramedics": (r"Paramedical Staff at SDHs and DHs", "Paramedical staff at SDHs and DHs"),
}


class IndiaHDIAdapter:
    name = "india_hdi"
    version = "1.0"

    def fetch(self) -> RawSnapshot:
        response = httpx.get(URL, timeout=40, follow_redirects=True)
        response.raise_for_status()
        parser = Paragraphs()
        parser.feed(response.content.decode("utf-8", errors="replace"))
        selected = [p for p in parser.paragraphs if p.startswith("As of March 31, 2023") or
                    p.startswith("These healthcare infrastructures are supported")]
        # PIB repeats the article in its accessible/print presentation.
        selected = list(dict.fromkeys(selected))
        if len(selected) != 2:
            raise ValueError("HDI publication structure changed: expected two quantitative paragraphs")
        return raw_snapshot(self.name, URL, "\n".join(selected), "text/plain",
            "Two quantitative paragraphs extracted from the official HTML; statistics as of 2023-03-31. Text whitespace normalized; numbers unchanged.")

    def normalize(self, raw: RawSnapshot) -> PublicDataset:
        raw.verify()
        if raw.adapter != self.name or str(raw.source_url) != URL:
            raise ValueError("Wrong source for the HDI adapter")
        if "As of March 31, 2023" not in raw.payload:
            raise ValueError("HDI reference date missing; do not silently assign a year")
        provenance = Provenance(id="india-hdi-2023", source_type="official_public",
            source_name="MoHFW Health Dynamics of India 2022–23, PIB national summary",
            source_url=URL, accessed_at=raw.accessed_at, geography=["IN"], is_synthetic=False,
            license="Government publication; factual statistical extract, attributed to MoHFW/PIB. No license identifier asserted.",
            methodology=raw.extraction, version=raw.version, checksum_sha256=raw.checksum_sha256)
        records = []
        for indicator, (pattern, label) in FIELDS.items():
            matches = re.findall(r"(?<![\d,])([\d,]+)\s+" + pattern, raw.payload)
            if len(matches) != 1:
                raise ValueError(f"HDI field missing or ambiguous: {indicator}")
            value = int(matches[0].replace(",", ""))
            if value <= 0:
                raise ValueError(f"HDI national aggregate must be positive: {indicator}")
            records.append(Observation(id=f"hdi-IN-{indicator}-2023", country_id="IN",
                indicator=indicator, label=label, year=2023, value=value, unit="count",
                provenance_id=provenance.id, source_record_id=f"PIB-2053070/{indicator}",
                note="National rural and urban aggregate as of 31 March 2023; not a live facility value."))
        return PublicDataset(adapter_version=self.version, provenance=provenance, records=records)
