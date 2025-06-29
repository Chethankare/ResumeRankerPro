import sqlite3
import bcrypt
from database import get_db_connection

class User:
    def __init__(self, email, password_hash, company=None, subscription_level="free", id=None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.company = company
        self.subscription_level = subscription_level
        
    @staticmethod
    def create(email, password, company=None):
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (email, password_hash, company)
                VALUES (?, ?, ?)
            ''', (email, password_hash, company))
            conn.commit()
            return User(email, password_hash, company, id=cursor.lastrowid)
    
    @staticmethod
    def get_by_email(email):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user_data = cursor.fetchone()
            if user_data:
                return User(
                    id=user_data['id'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash'],
                    company=user_data['company'],
                    subscription_level=user_data['subscription_level']
                )
        return None
    
    def verify_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def get_subscription_limit(self):
        limits = {
            "free": 20,
            "pro": 50,
            "enterprise": 200
        }
        return limits.get(self.subscription_level, 20)

class Job:
    @staticmethod
    def create(user_id, job_title, job_description):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO jobs (user_id, job_title, job_description)
                VALUES (?, ?, ?)
            ''', (user_id, job_title, job_description))
            conn.commit()
            return cursor.lastrowid

class Analysis:
    @staticmethod
    def save_results(user_id, job_id, results):
        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO analyses (user_id, job_id, results)
                VALUES (?, ?, ?)
            ''', (user_id, job_id, results))
            conn.commit()
    
    @staticmethod
    def get_history(user_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.id, j.job_title, a.created_at 
                FROM analyses a
                JOIN jobs j ON a.job_id = j.id
                WHERE a.user_id = ?
                ORDER BY a.created_at DESC
            ''', (user_id,))
            return cursor.fetchall()