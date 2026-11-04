from app.database.firestore import get_db
from loguru import logger
from datetime import datetime

class FirestoreRepository:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.db = None
        try:
            self.db = get_db()
        except Exception as e:
            logger.warning(f"Firestore not initialized. Repository {collection_name} will run in mocked mode.")

    def _get_collection(self, user_id: str):
        if not self.db:
            return None
        return self.db.collection("users").document(user_id).collection(self.collection_name)

    def create(self, user_id: str, data: dict, doc_id: str = None):
        if not self.db:
            logger.info(f"[MOCK] Created doc in users/{user_id}/{self.collection_name} with id {doc_id}")
            return doc_id or "mock_id"
        
        try:
            coll = self._get_collection(user_id)
            if doc_id:
                coll.document(doc_id).set(data)
                return doc_id
            else:
                doc_ref = coll.document()
                doc_ref.set(data)
                return doc_ref.id
        except Exception as e:
            logger.error(f"Error creating doc in users/{user_id}/{self.collection_name}: {e}")
            raise e

    def get_by_user(self, user_id: str, limit: int = 10, order_by: str = "timestamp", descending: bool = True):
        if not self.db:
            return []
            
        try:
            query = self._get_collection(user_id)
            if order_by:
                query = query.order_by(order_by, direction="DESCENDING" if descending else "ASCENDING")
            if limit:
                query = query.limit(limit)
                
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Error querying users/{user_id}/{self.collection_name}: {e}")
            return []

# Dedicated Repositories
class PredictionsRepository(FirestoreRepository):
    def __init__(self):
        super().__init__("predictions")

class ExplanationsRepository(FirestoreRepository):
    def __init__(self):
        super().__init__("explanations")

class AlertsRepository(FirestoreRepository):
    def __init__(self):
        super().__init__("alerts")

class RawReadingsRepository(FirestoreRepository):
    def __init__(self):
        super().__init__("raw_readings")
