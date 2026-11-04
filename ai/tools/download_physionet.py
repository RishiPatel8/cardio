import os
import csv
import logging

try:
    import wfdb
except ImportError:
    wfdb = None

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class PhysioNetDownloader:
    def __init__(self, target_dir="ai/data/raw/physionet_mitbih", metadata_dir="ai/data/metadata"):
        self.target_dir = target_dir
        self.metadata_dir = metadata_dir
        self.dataset_name = "mitdb"
        
        os.makedirs(self.target_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)

    def download_database(self):
        if wfdb is None:
            logger.error("BLOCKED: The 'wfdb' package is not installed in the environment.")
            logger.error("Cannot download or parse original PhysioNet records without this dependency.")
            return False
            
        logger.info(f"Initiating download of {self.dataset_name} to {self.target_dir}")
        try:
            # Download exactly the MIT-BIH Arrhythmia Database
            wfdb.dl_database(self.dataset_name, dl_dir=self.target_dir)
            logger.info("Download completed successfully.")
            self._generate_manifest()
            return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

    def _generate_manifest(self):
        """Builds ai/data/metadata/physionet_manifest.csv strictly tracking Record vs Patient ID."""
        manifest_path = os.path.join(self.metadata_dir, "physionet_manifest.csv")
        records = wfdb.get_record_list(self.dataset_name)
        
        with open(manifest_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "record_id", 
                "patient_id", 
                "sampling_rate", 
                "number_of_samples", 
                "channels", 
                "annotation_availability", 
                "source_dataset", 
                "dataset_version"
            ])
            
            for record_name in records:
                try:
                    # In MIT-BIH, record_id serves as the subject/patient identifier, except that
                    # record 201 and 202 are from the same patient.
                    patient_id = "patient_201_202" if record_name in ["201", "202"] else f"patient_{record_name}"
                    
                    record = wfdb.rdheader(os.path.join(self.target_dir, record_name))
                    writer.writerow([
                        record_name,
                        patient_id,
                        record.fs,
                        record.sig_len,
                        ",".join(record.sig_name),
                        "YES",
                        "PhysioNet MIT-BIH",
                        "1.0.0"
                    ])
                except Exception as e:
                    logger.warning(f"Could not parse header for record {record_name}: {e}")
                    
        logger.info(f"Generated patient manifest at {manifest_path}")

if __name__ == "__main__":
    downloader = PhysioNetDownloader()
    downloader.download_database()
