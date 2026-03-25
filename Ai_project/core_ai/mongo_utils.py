from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from django.conf import settings

def get_mongo_client():
    """Returns a MongoClient instance."""
    try:
        client = MongoClient(
            host=settings.MONGO_HOST,
            port=settings.MONGO_PORT,
            serverSelectionTimeoutMS=5000  # 5 seconds timeout
        )
        client.admin.command('ping')
        return client
    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {e}")
        return None

def get_mongo_db():
    """Returns the MongoDB database instance."""
    client = get_mongo_client()
    if client is not None:
        return client[settings.MONGO_DB_NAME]
    return None
