# Import all the models, so that Base has them before being
# imported by Alembic or script executors
from app.database.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.wearable_data import WearableData  # noqa
from app.models.health_score import HealthScore  # noqa
from app.models.prediction import Prediction  # noqa
from app.models.prediction_history import PredictionHistory  # noqa
from app.models.report import Report  # noqa
from app.models.notification import Notification  # noqa
from app.models.emergency_contact import EmergencyContact  # noqa
from app.models.settings import Settings  # noqa
from app.models.user_profile import UserProfile  # noqa
from app.models.nutrition_log import NutritionLog  # noqa
from app.models.hydration_log import HydrationLog  # noqa
from app.models.medication_reminder import MedicationReminder  # noqa
from app.models.doctor_note import DoctorNote  # noqa
from app.models.timeline_event import TimelineEvent  # noqa
from app.models.wearable_device import WearableDevice  # noqa
from app.models.privacy_consent import PrivacyConsent  # noqa
from app.models.background_job import BackgroundJob  # noqa
