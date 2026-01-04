
import pandas as pd
import requests
import io

url = "https://opendata-ajuntament.barcelona.cat/data/dataset/d395e808-697d-4722-8eb9-b672a8ba0916/resource/2d190658-93ac-4c43-a23f-c5d313b1ae9c/download"
response = requests.get(url)
df = pd.read_csv(io.BytesIO(response.content))
print(f"Columns: {list(df.columns)}")
print(df.head())
