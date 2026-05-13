from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

# -----------------------------
# User（一般ユーザー）
# -----------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)

    zipcode = db.Column(db.String(8))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))

    membership_status = db.Column(db.String(20), default='活動中')  
    # active / inactive / withdrawn などfrom datetime import datetime, timezone

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # パスワード設定
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # パスワードチェック
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Flask-Login 用
    def get_id(self):
        return str(self.id)


# -----------------------------
# Admin（管理者ユーザー）
# -----------------------------
class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # パスワード設定
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # パスワードチェック
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Flask-Login 用
    def get_id(self):
        return str(self.id)

# -----------------------------
# mail_logs（mailログ）
# -----------------------------
class MailLog(db.Model):
    __tablename__ = 'mail_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    mail_type = db.Column(db.String(50), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # User とのリレーション（便利）
    user = db.relationship('User', backref=db.backref('mail_logs', lazy=True))
