import os
from datetime import datetime as dt
from enum import Enum
from typing import Any

import redis
from flask import Flask, json
from redis import Redis

from app.db_crud import crud_ticket
from app.db_models import Ticket, TicketStatus, db


REDIS_CLIENT = redis.Redis().from_url(
    url=os.environ['REDIS_URL'],
    encoding='utf-8',
    decode_responses=True,
    username=os.environ['REDIS_USER'],
    password=os.environ['REDIS_PASSWORD'],
)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "default")
    app.config['SQLALCHEMY_DATABASE_URI'] = ''.join(
        (
            f"postgresql://{os.environ['POSTGRES_USER']}:",
            f"{os.environ['POSTGRES_PASSWORD']}@db:5432/",
            f"{os.environ['POSTGRES_DB']}",
        )
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    app.app_context().push()
    db.create_all()
    return app


def db_obj_to_dict(obj: db.Model) -> dict:
    return {
        column.name: getattr(obj, column.name)
        for column in obj.__table__.columns
    }


def custom_encoder(obj: Any) -> str:
    if isinstance(obj, dt):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.name


def check_ticket_status(
    current_status: TicketStatus, new_status: TicketStatus
) -> bool:
    return (
        new_status in (TicketStatus.answered, TicketStatus.closed)
        and (
            current_status == TicketStatus.opened
            or current_status == TicketStatus.awaited
        )
        or new_status in (TicketStatus.awaited, TicketStatus.closed)
        and current_status == TicketStatus.answered
    )


def get_ticket_response(ticket_id: int, redis_client: Redis) -> str:
    ticket = redis_client.get(f'ticket_{ticket_id}')
    if not ticket:
        ticket = crud_ticket.get(obj_id=ticket_id)
    comments = redis_client.mget(
        redis_client.scan(match=f'ticket_{ticket_id}_comment_*')[-1]
    )
    if comments:
        comments = {'comments': [json.loads(comment) for comment in comments]}
    else:
        comments = {
            'comments': [
                db_obj_to_dict(comment) for comment in ticket.comments
            ]
            if isinstance(ticket, Ticket)
            else []
        }
    if isinstance(ticket, Ticket):
        return json.dumps(
            {**db_obj_to_dict(ticket), **comments},
            default=custom_encoder,
        )
    return json.dumps(
        {**json.loads(ticket), **comments}, default=custom_encoder
    )
