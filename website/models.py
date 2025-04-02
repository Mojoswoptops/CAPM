from flask_sqlalchemy import SQLAlchemy
from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    jobs = db.relationship('Job', backref='user', lazy=True)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_first_name = db.Column(db.String(100), nullable=False)
    customer_last_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120))  # New field for customer email
    address_street = db.Column(db.String(200), nullable=False)
    address_suburb = db.Column(db.String(100), nullable=False)
    address_city = db.Column(db.String(100), nullable=False)
    address_state = db.Column(db.String(50), nullable=False)
    address_postcode = db.Column(db.String(10), nullable=False)  # New field for postcode
    budget = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    stage = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cost_items = db.relationship('CostItem', backref='job', lazy=True)

class CostItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cost_code = db.Column(db.String(50))
    description = db.Column(db.String(200))
    qty = db.Column(db.Float)  # New field for quantity
    unit = db.Column(db.String(20))  # New field for unit
    value = db.Column(db.Float)  # New field for value
    budget = db.Column(db.Float)
    committed_cost = db.Column(db.Float)
    actual_cost = db.Column(db.Float)
    cost_to_complete = db.Column(db.Float)
    forecast_at_completion = db.Column(db.Float)
    gain_loss = db.Column(db.Float)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)