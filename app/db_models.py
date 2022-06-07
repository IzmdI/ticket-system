from datetime import datetime as dt
from enum import Enum

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class TicketStatus(Enum):
    opened = 'opened'
    closed = 'closed'
    awaited = 'awaited'
    answered = 'answered'


class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True, index=True)
    created_at = db.Column(db.DateTime, index=True, default=dt.utcnow())
    updated_at = db.Column(db.DateTime, index=True, default=dt.utcnow())
    theme = db.Column(db.String, index=True)
    text = db.Column(db.String)
    email = db.Column(db.String(length=255), index=True)
    status = db.Column(
        db.Enum(TicketStatus),
        default=TicketStatus.opened,
        index=True,
        nullable=False,
    )
    comments = db.relationship('Comment', cascade='all,delete')


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True, index=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'))
    created_at = db.Column(db.DateTime, index=True, default=dt.utcnow())
    email = db.Column(db.String(length=255), index=True)
    text = db.Column(db.String)
