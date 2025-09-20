from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

class Family(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    name = db.Column(db.String(100), nullable=False)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'))
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date)
    gender = db.Column(db.String(10))
    mobile = db.Column(db.String(15))
    wedding_date = db.Column(db.Date)
    is_deceased = db.Column(db.Boolean, default=False)
    relation = db.Column(db.String(20))  # father, mother, child

class TaxRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    year = db.Column(db.Integer)
    term = db.Column(db.Integer)  # 1 or 2
    amount = db.Column(db.Float)
    paid_on = db.Column(db.Date)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))  # admin, group_leader, viewer
