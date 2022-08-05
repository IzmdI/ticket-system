import os

import redis
from flask import Flask

from app.db_models import TicketStatus, db


def get_redis_client():
    client = redis.Redis().from_url(
        url=os.environ['REDIS_URL'],
        encoding='utf-8',
        decode_responses=True,
        username=os.environ['REDIS_USER'],
        password=os.environ['REDIS_PASSWORD'],
    )
    return client


def create_app(for_tests: bool = False) -> Flask:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default')
    if for_tests:
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = ''.join(
            (
                f"postgresql://{os.environ['POSTGRES_USER']}:",
                f"{os.environ['POSTGRES_PASSWORD']}@db:5432/",
                f"{os.environ['POSTGRES_DB']}",
            ),
        )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    app.app_context().push()
    db.create_all()
    return app


def check_ticket_status(
    current_status: TicketStatus,
    new_status: TicketStatus,
) -> bool:
    if current_status in (TicketStatus.opened, TicketStatus.awaited):
        return new_status in (TicketStatus.answered, TicketStatus.closed)
    if current_status == TicketStatus.answered:
        return new_status in (TicketStatus.awaited, TicketStatus.closed)
    return False
