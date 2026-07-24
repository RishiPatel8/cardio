from pydantic import BaseModel

class HealthCheckResponse(BaseModel):
    status: str
    database: str
    cache: str
    version: str
