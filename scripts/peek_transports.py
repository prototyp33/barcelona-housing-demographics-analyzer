
import pandas as pd
import requests
import io

url = "https://opendata-ajuntament.barcelona.cat/data/dataset/e0c34739-823f-470d-8045-e10f28e80f2d/resource/e07dec0d-4aeb-40f3-b987-e1f35e088ce2/download"
response = requests.get(url)
df = pd.read_csv(io.BytesIO(response.content))
print(f"Columns: {list(df.columns)}")
print(df.head())
