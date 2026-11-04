import os
import sys
import requests
import zipfile
import subprocess
try:
    from loguru import logger
except ImportError:
    import logging as logger
    logger.basicConfig(level=logger.INFO)

class DatasetDownloader:
    def __init__(self, data_dir: str = "d:/cardiogaurd/ai/datasets"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
    def download_kaggle_mitbih(self):
        """
        Attempts to download the MIT-BIH dataset using the Kaggle CLI.
        Requires Kaggle API credentials (kaggle.json) to be configured in ~/.kaggle/
        """
        dataset_name = "shayanfazeli/heartbeat"
        target_path = os.path.join(self.data_dir, "mitbih_train.csv")
        
        if os.path.exists(target_path):
            logger.info("MIT-BIH dataset already exists locally.")
            return True
            
        logger.info(f"Attempting to download {dataset_name} via Kaggle API...")
        try:
            # Using subprocess to call the kaggle module
            result = subprocess.run(
                [sys.executable, "-m", "kaggle", "datasets", "download", "-d", dataset_name, "-p", self.data_dir, "--unzip"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                logger.info("Dataset downloaded and unzipped successfully.")
                return True
            else:
                logger.error(f"Kaggle download failed: {result.stderr}")
                logger.warning("Please download manually from https://www.kaggle.com/datasets/shayanfazeli/heartbeat and extract to ai/datasets/")
                return False
        except Exception as e:
            logger.error(f"Error executing kaggle command: {e}")
            logger.warning("Please install kaggle cli ('pip install kaggle') and configure credentials, or download manually.")
            return False

if __name__ == "__main__":
    downloader = DatasetDownloader()
    downloader.download_kaggle_mitbih()
