# Normalized public observations

`india_hdi.json` contains 13 dated national counts. `who_gho.json` contains 20 historical country/indicator/year observations. Each record links to public provenance and retains units and reference year.

Regenerate with `python scripts/import_official_data.py` from the repository root. This uses attributed raw caches without network access; `--refresh` explicitly downloads current source selections. Records are schema-validated and checked against their raw payload and adapter output. Do not edit numeric values here by hand. Synthetic operations belong in `data/generated`.
