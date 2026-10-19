# DocMindX AI Dataset Package v2.0.0

Build date: 2026-10-16
Source: user-supplied `datasets.zip`

## Changes

1. Preserved existing symptom IDs and existing disease/symptom clinical mappings. No guessed disease-symptom associations, prescriptions, treatment schedules, or new diagnoses were added.
2. Resolved four exact translated-label collisions in `symptoms/symptoms_master.csv` (two Hindi/Gujarati concepts and two urinary-symptom concepts). The existing IDs and all unrelated columns are unchanged. Edits are listed in `data_quality/localized_label_collision_resolution.csv`.
3. Added `symptoms/symptom_aliases.csv`, a traceable index of exact labels already present in the canonical master (`en`, `hi`, `gu`). It contains no generated transliteration phrases. The application must load and validate this file to use it as an alias index; adding this file alone does not change runtime code.
4. Added `symptoms/symptom_aliases_review_queue_template.csv` for reviewed additions. Do not automatically activate unreviewed aliases.
5. The source archive contained two conflicting copies of `india_major_diseases.csv`: 85 rows under `disease/` and a nested 36-row subset under `datasets/disease/`. The 85-row `disease/india_major_diseases.csv` was retained as canonical; the nested active copy is now an exact mirror. The old 36-row subset is preserved under `data_quality/archive/legacy_nested_india_major_diseases_36rows.csv` for human review, not runtime loading.
6. Preserved the original primary Parquet and synchronized the nested compatibility copy to that same file. The old 36-row nested Parquet is archived. The environment lacked a Parquet engine to independently read/verify Parquet row contents; see `DATASET_VERSION.json`.
7. Added data-quality reports for translation coverage, mapping gaps, and structural validation. Unmapped records are reported, not auto-filled, because clinical mappings require evidence and medical review.

## Known limits

- The master currently supplies native-script labels only for English, Hindi, and Gujarati. Do not claim full offline coverage for other configured languages without verified aliases or an appropriate local model.
- Romanized/colloquial aliases are not fabricated. Add them via the review queue with a defensible source and review before activating them.
- Existing records retain draft/source labels and must receive appropriate clinical review before production clinical decision support.
- Existing dataset generator scripts were not rewritten; inspect their output behavior before rerunning them, because generation may overwrite manual dataset edits.
- This is a data package update, not an application-code patch. The extractor must be updated to consume the new alias catalog and distinguish unresolved/ambiguous matches.

## Validation

Run from repository root:

```bash
python datasets/data_quality/validate_dataset_v2.py
```

The validator checks IDs, mapping references, duplicate keys, localized label uniqueness, alias references, and canonical-copy consistency. It does not prove medical correctness.
