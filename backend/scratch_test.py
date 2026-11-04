import asyncio
import uuid
import sys
from app.schemas.prediction import PredictionRequest
from app.services.prediction import PredictionService
from app.database.session import async_session_maker
import json
import logging
import traceback

logging.basicConfig(level=logging.DEBUG)

async def main():
    try:
        # read the test_ecg.csv
        with open("../docs/test_ecg.csv", "r", encoding="utf-16le") as f:
            lines = f.readlines()
        
        raw_signal = []
        for line in lines:
            for val in line.split(','):
                try:
                    raw_signal.append(float(val.strip()))
                except:
                    pass

        print(f"Loaded {len(raw_signal)} values from test_ecg.csv")
        
        request = PredictionRequest(
            telemetry_id=uuid.uuid4(),
            avg_bpm=75.0,
            sdrr_ms=45.0,
            rmssd_ms=35.0,
            raw_ecg=raw_signal,
            fs=100.0
        )
        
        async with async_session_maker() as db:
            service = PredictionService(db=db)
            pred = await service.generate_ai_prediction(uuid.uuid4(), request)
            print("Success!", pred.classification)
            
    except Exception as e:
        print(f"Failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
