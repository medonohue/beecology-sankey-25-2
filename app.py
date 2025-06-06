
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI()

# Allow access from any frontend (e.g., Netlify)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Public CSV export link for the Google Sheet
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1G-u7xTsMFKGJYmaQ8AYEYtLHl9va4c69/export?format=csv"

@app.get("/sankey-data")
def get_sankey_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        df = df[['species', 'flower_family']].dropna()
        df = df[df['flower_family'].str.lower() != 'unknown']
        grouped = df.groupby(['species', 'flower_family']).size().reset_index(name='count')

        # Normalize: Scale left side to match right side total
        bee_totals = grouped.groupby('species')['count'].sum().sum()
        flower_totals = grouped.groupby('flower_family')['count'].sum().sum()
        scaling_factor = flower_totals / bee_totals if bee_totals < flower_totals else 1
        grouped['count'] *= scaling_factor

        labels = pd.unique(grouped[['species', 'flower_family']].values.ravel())
        label_map = {label: i for i, label in enumerate(labels)}
        nodes = [{"name": label} for label in labels]

        links = [
            {
                "source": label_map[row['species']],
                "target": label_map[row['flower_family']],
                "value": row['count']
            }
            for _, row in grouped.iterrows()
        ]

        return {"nodes": nodes, "links": links}

    except Exception as e:
        return {"error": str(e)}
