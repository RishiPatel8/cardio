import urllib.request
import zipfile
import os

url = "https://physionet.org/static/published-projects/ptb-xl/ptb-xl-a-large-publicly-available-electrocardiography-dataset-1.0.3.zip"
zip_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'ptbxl.zip'))
extract_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scratch', 'ptbxl'))

print(f"Downloading {url} to {zip_path}...")
urllib.request.urlretrieve(url, zip_path)

print(f"Extracting {zip_path} to {extract_dir}...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

print("Done extracting zip!")
