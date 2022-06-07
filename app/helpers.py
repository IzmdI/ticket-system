import os
from typing import Optional

import redis
from flask import Flask, json

from app.db_crud import crud_ticket
from app.db_models import Ticket, TicketStatus, db
from app.db_schemas import comment_schema, ticket_schema
import fakeredis


def get_redis_client():
    # client = redis.Redis().from_url(
    #     url=os.environ['REDIS_URL'],
    #     encoding='utf-8',
    #     decode_responses=True,
    #     username=os.environ['REDIS_USER'],
    #     password=os.environ['REDIS_PASSWORD'],
    # )
    client = fakeredis.FakeRedis()
    return client


def create_app(for_tests: bool = False) -> Flask:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "default")
    if for_tests:
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        # app.config['SQLALCHEMY_DATABASE_URI'] = ''.join(
        #     (
        #         f"postgresql://{os.environ['POSTGRES_USER']}:",
        #         f"{os.environ['POSTGRES_PASSWORD']}@db:5432/",
        #         f"{os.environ['POSTGRES_DB']}",
        #     )
        # )
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    app.app_context().push()
    db.create_all()
    return app


def check_ticket_status(
    current_status: TicketStatus, new_status: TicketStatus
) -> bool:
    if current_status in (TicketStatus.opened, TicketStatus.awaited):
        return new_status in (TicketStatus.answered, TicketStatus.closed)
    if current_status == TicketStatus.answered:
        return new_status in (TicketStatus.awaited, TicketStatus.closed)
    return False


def get_ticket_as_dict(ticket_id: int, obj: Optional[Ticket] = None) -> dict:
    if obj:
        return ticket_schema.dump(obj)
    redis_client = get_redis_client()
    ticket = redis_client.get(f'ticket_{ticket_id}')
    if not ticket:
        redis_client.close()
        ticket = crud_ticket.get(db=db.session, obj_id=ticket_id)
        if not ticket:
            return {}
        return ticket_schema.dump(ticket)
    comments = redis_client.mget(
        redis_client.scan(match=f'ticket_{ticket_id}_comment_*')[-1]
    )
    redis_client.close()
    comments = {'comments': [json.loads(comment) for comment in comments]}
    return {**json.loads(ticket), **comments}  # noqa


def get_comment_as_dict(comment) -> dict:
    return comment_schema.dump(comment)
