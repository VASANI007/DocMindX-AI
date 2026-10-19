#!/usr/bin/env python3
"""Basic structural validation for DocMindX AI datasets v2.0.0.
This checks data integrity, not clinical correctness.
Run from repository root: python datasets/data_quality/validate_dataset_v2.py
"""
from pathlib import Path
import json, sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
def load(rel): return pd.read_csv(ROOT/rel, dtype=str, keep_default_na=False, low_memory=False)
s=load('symptoms/symptoms_master.csv')
d=load('disease/disease_master.csv')
m=load('disease/disease_symptom_mapping.csv')
a=load('symptoms/symptom_aliases.csv')
major=load('disease/india_major_diseases.csv')
nested=load('datasets/disease/india_major_diseases.csv')
errors=[]
if s['symptom_id'].duplicated().any(): errors.append('Duplicate symptom_id in symptoms_master.csv')
if s['symptom_name'].str.strip().str.casefold().duplicated().any(): errors.append('Duplicate English symptom names')
for col,lang in [('symptom_name_hi','Hindi'),('symptom_name_gu','Gujarati')]:
 vals=s[col].str.strip().str.casefold(); vals=vals[vals.ne('')]
 if vals.duplicated().any(): errors.append(f'Duplicate non-empty {lang} labels')
known_s=set(s.symptom_id.str.strip()); known_d=set(d.disease_id.str.strip())
if set(m.symptom_id.str.strip())-known_s: errors.append('Mapping references unknown symptom IDs')
if set(m.disease_id.str.strip())-known_d: errors.append('Mapping references unknown disease IDs')
if m.duplicated(['disease_id','symptom_id']).any(): errors.append('Duplicate disease-symptom pairs')
if set(a.symptom_id.str.strip())-known_s: errors.append('Alias catalog references unknown symptom IDs')
if len(major)!=len(nested) or list(major.columns)!=list(nested.columns) or not major.astype(str).reset_index(drop=True).equals(nested.astype(str).reset_index(drop=True)):
 errors.append('Nested major-diseases file is not an exact mirror of canonical CSV')
if errors:
 print('FAIL')
 for e in errors: print('-',e)
 sys.exit(1)
print('PASS: structural dataset checks')
print(f'Symptoms={len(s)}, Diseases={len(d)}, Mappings={len(m)}, Alias labels={len(a)}, Major diseases={len(major)}')
print('NOTE: These checks do not establish clinical validity of diseases, translations, treatments, or mappings.')
