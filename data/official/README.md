# Attributed public-source caches

`india/hdi-2023.json` contains the two factual quantitative paragraphs extracted from the MoHFW/PIB Health Dynamics of India 2022–23 summary. `who/brics-indicators.json` contains 20 selected original WHO GHO indicator records. Both were fetched on September 27, 2026, with source/request URLs, hashes and metadata retained.

These are actual historical public records, not invented fixtures or live operational data. The India cache is a factual summary extract, not the full government publication. WHO's cache is a small selected subset, not its entire dataset. Original public material retains its own terms and is not relicensed under the project's MIT license. WHO does not endorse this project.

See [sources, attribution and terms](../../docs/data-sources.md). Run `python scripts/import_official_data.py` for offline normalization or add `--refresh` to fetch actual source endpoints. Missing caches lead to visible fallback assumptions; invalid caches fail validation. Generated facility operations belong in `data/generated`, never here.
