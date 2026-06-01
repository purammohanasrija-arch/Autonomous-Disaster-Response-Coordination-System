"""
User model — backed by MongoDB users collection.
"""
from flask_login import UserMixin
from bson import ObjectId
from .database import get_mongo_db


class User(UserMixin):
    def __init__(self, id, username, email, phone=None):
        self.id       = str(id)
        self.username = username
        self.email    = email
        self.phone    = phone

    @staticmethod
    def get_by_id(user_id):
        try:
            db  = get_mongo_db()
            doc = db.users.find_one({'_id': ObjectId(str(user_id))})
            if doc:
                return User(doc['_id'], doc['username'], doc['email'], doc.get('phone'))
        except Exception:
            pass
        return None

    @staticmethod
    def get_by_username(username):
        try:
            db = get_mongo_db()
            return db.users.find_one({'username': username})
        except Exception:
            return None

    @staticmethod
    def get_by_email(email):
        try:
            db = get_mongo_db()
            return db.users.find_one({'email': email})
        except Exception:
            return None
