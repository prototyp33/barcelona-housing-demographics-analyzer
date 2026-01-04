
import pandas as pd
import requests
import io

url = "https://opendata-ajuntament.barcelona.cat/data/dataset/parcs-i-jardins/resource/a933230a-9d92-4f36-932f-7634f107384a/download/opendatabcn_cultura_parcs-i-jardins.csv"
response = requests.get(url)
# Detection of encoding
df = pd.read_csv(io.BytesIO(response.content), encoding='utf-16')
print(f"Columns: {list(df.columns)}")
print(df.head())
