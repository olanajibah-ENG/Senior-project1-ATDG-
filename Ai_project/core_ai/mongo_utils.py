from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from gridfs import GridFS
from django.conf import settings


def get_mongo_client():
    """Returns a MongoClient instance."""
    try:
        client = MongoClient(
            host=settings.MONGO_HOST,
            port=settings.MONGO_PORT,
            serverSelectionTimeoutMS=5000
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


def get_gridfs():
    """
    Returns a GridFS instance للتخزين والاسترجاع.
    GridFS بيقسم الملفات الكبيرة لـ chunks بحجم 255KB.
    """
    db = get_mongo_db()
    if db is None:
        return None
    return GridFS(db)


def save_to_gridfs(content: str, filename: str, metadata: dict = None) -> str:
    """
    يحفظ محتوى نصي في GridFS ويرجع الـ file_id كـ string.

    Args:
        content:  محتوى الملف كـ string
        filename: اسم الملف
        metadata: بيانات إضافية (project_id, file_type, إلخ)

    Returns:
        str: الـ ObjectId الخاص بالملف في GridFS
    """
    fs = get_gridfs()
    if fs is None:
        raise Exception("GridFS connection failed")

    encoded = content.encode('utf-8')
    file_id = fs.put(
        encoded,
        filename=filename,
        metadata=metadata or {}
    )
    return str(file_id)


def read_from_gridfs(gridfs_id: str) -> str:
    """
    يجيب محتوى ملف من GridFS بالـ file_id.

    Args:
        gridfs_id: الـ ObjectId الخاص بالملف في GridFS

    Returns:
        str: محتوى الملف كـ string
    """
    from bson import ObjectId

    fs = get_gridfs()
    if fs is None:
        raise Exception("GridFS connection failed")

    grid_out = fs.get(ObjectId(gridfs_id))
    return grid_out.read().decode('utf-8')


def delete_from_gridfs(gridfs_id: str) -> None:
    """
    يحذف ملف من GridFS بالـ file_id.
    """
    from bson import ObjectId

    fs = get_gridfs()
    if fs is None:
        raise Exception("GridFS connection failed")

    fs.delete(ObjectId(gridfs_id))