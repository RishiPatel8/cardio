from fastapi import APIRouter

router = APIRouter()

@router.get("/metrics")
async def get_research_metrics():
    """
    Public endpoint for research metrics.
    """
    return {
        "dataset": "MIT-BIH (shayanfazeli/heartbeat)",
        "models_evaluated": ["CNN+LSTM", "Random Forest", "CNN", "LSTM"],
        "metrics_note": "Based on 5% training subset",
        "best_f1": 0.8333,
        "best_model": "Random Forest"
    }
