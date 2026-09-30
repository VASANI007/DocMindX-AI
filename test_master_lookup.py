import pandas as pd
df = pd.read_csv('datasets/symptoms/symptoms_master.csv')
print('Total symptoms in master:', len(df))
for q in ['fever', 'headache', 'sore throat', 'pharyngitis', 'dizziness', 'vertigo', 'joint pain', 'leg pain', 'body ache']:
    m = df[df['symptom_name'].str.lower().str.contains(q)]
    print(f'Query "{q}" matches: {len(m)}')
    for _, r in m.head(2).iterrows():
        print(f'  {r["symptom_id"]}: {r["symptom_name"]}')
