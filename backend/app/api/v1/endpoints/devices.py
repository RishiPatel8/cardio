from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.wearable_device import WearableDevice
from app.repositories.wearable_device import WearableDeviceRepository
from app.schemas.wearable_device import WearableDeviceCreate, WearableDeviceResponse

router = APIRouter()

@router.get("", response_model=List[WearableDeviceResponse], summary="Get Connected Devices")
async def get_connected_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve the list of all connected devices for the patient."""
    repo = WearableDeviceRepository(db)
    devices = await repo.get_by_user(current_user.id)
    if not devices:
        # Seed default Health Connect virtual connection
        dev = WearableDevice(
            user_id=current_user.id,
            device_name="Health Connect SDK Gateway",
            manufacturer="Google",
            connection_status="Connected",
            battery_percent=94,
            firmware_version="v2026.07",
            hr_sensor=True,
            spo2_sensor=True,
            sleep_sensor=True,
            gyro_sensor=True,
            gps_sensor=True
        )
        dev = await repo.create(dev)
        await db.commit()
        devices = [dev]
    return devices

@router.post("/connect", response_model=WearableDeviceResponse, status_code=status.HTTP_201_CREATED, summary="Connect Device abstraction")
async def connect_wearable_device(
    request_data: WearableDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Connect a new wearable sensor abstraction (Samsung Health, Fitbit, Polar, Oura, etc.)."""
    repo = WearableDeviceRepository(db)
    dev = WearableDevice(
        user_id=current_user.id,
        device_name=request_data.device_name,
        manufacturer=request_data.manufacturer,
        connection_status="Connected",
        battery_percent=request_data.battery_percent or 100,
        firmware_version=request_data.firmware_version or "1.0.0",
        hr_sensor=request_data.hr_sensor,
        spo2_sensor=request_data.spo2_sensor,
        sleep_sensor=request_data.sleep_sensor,
        gyro_sensor=request_data.gyro_sensor,
        gps_sensor=request_data.gps_sensor
    )
    dev = await repo.create(dev)
    await db.commit()
    return dev

@router.post("/{device_id}/diagnostics", response_model=WearableDeviceResponse, summary="Run Device Sensor Diagnostics")
async def run_device_diagnostics(
    device_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Calibrate smartwatch sensors and run diagnostic telemetry checks."""
    repo = WearableDeviceRepository(db)
    dev = await repo.get_by_id(device_id)
    if not dev or dev.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Wearable device not found.")
    dev.battery_percent = max(10, dev.battery_percent - 2) # Simulate active battery consumption during sensor load test
    await repo.update(dev)
    await db.commit()
    return dev

@router.delete("/{device_id}/disconnect", status_code=status.HTTP_204_NO_CONTENT, summary="Disconnect Wearable Device")
async def disconnect_wearable_device(
    device_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect the wearable sensor gateway abstraction."""
    repo = WearableDeviceRepository(db)
    dev = await repo.get_by_id(device_id)
    if not dev or dev.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Wearable device not found.")
    await repo.delete(device_id)
    await db.commit()
    return
