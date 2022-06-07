import os
from typing import Optional

import redis
from flask import Flask, json
from redis import Redis

from app.db_crud import crud_ticket
from app.db_models import Ticket, TicketStatus, db
from app.db_schemas import comment_schema, ticket_schema


# REDIS_CLIENT = redis.Redis().from_url(
#     url=os.environ['REDIS_URL'],
#     encoding='utf-8',
#     decode_responses=True,
#     username=os.environ['REDIS_USER'],
#     password=os.environ['REDIS_PASSWORD'],
# )
REDIS_CLIENT = redis.Redis()


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
    return (
        new_status in (TicketStatus.answered, TicketStatus.closed)
        and (
            current_status == TicketStatus.opened
            or current_status == TicketStatus.awaited
        )
        or new_status in (TicketStatus.awaited, TicketStatus.closed)
        and current_status == TicketStatus.answered
    )


def get_ticket_json(
    ticket_id: int, redis_client: Redis, obj: Optional[Ticket] = None
) -> str:
    if obj:
        return json.dumps(ticket_schema.dump(obj))
    ticket = redis_client.get(f'ticket_{ticket_id}')
    if not ticket:
        ticket = crud_ticket.get(obj_id=ticket_id)
        return json.dumps(ticket_schema.dump(ticket))
    comments = redis_client.mget(
        redis_client.scan(match=f'ticket_{ticket_id}_comment_*')[-1]
    )
    comments = {'comments': [json.loads(comment) for comment in comments]}
    return json.dumps({**json.loads(ticket), **comments})


def get_comment_json(comment) -> str:
    return json.dumps(comment_schema.dump(comment))
