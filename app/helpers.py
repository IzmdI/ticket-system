from datetime import datetime as dt
from enum import Enum
from typing import Any

from flask import Flask, json
from redis import Redis

from db_models import Comment, Ticket, TicketStatus, db


def create_app():
    app = Flask(__name__)
    #  TODO: move it to .env
    app.config['SECRET_KEY'] = 'supersecretkey'
    app.config[
        'SQLALCHEMY_DATABASE_URI'
    ] = 'postgresql://postgres:postgres@localhost:5432/tickets'
    app.config['REDIS_EXPIRE_TIME'] = 60 * 2
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    app.app_context().push()
    return app


def db_obj_to_dict(obj: db.Model) -> dict:
    return {
        column.name: getattr(obj, column.name)
        for column in obj.__table__.columns
    }


def custom_encoder(obj: Any) -> Any:
    if isinstance(obj, dt):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.name


def check_ticket_status(
    current_status: TicketStatus, new_status: TicketStatus
) -> bool:
    return (
        current_status == TicketStatus.opened
        or current_status == TicketStatus.awaited
        and new_status in (TicketStatus.answered, TicketStatus.closed)
        or current_status == TicketStatus.answered
        and new_status in (TicketStatus.awaited, TicketStatus.closed)
    )


def get_ticket_response(ticket_id: int, redis_client: Redis):
    ticket = redis_client.get(f'ticket_{ticket_id}')
    if ticket:
        ticket = ticket.decode('utf-8')
    else:
        ticket = Ticket.query.get_or_404(ticket_id)
    comments = redis_client.mget(
        redis_client.scan(match=f'ticket_{ticket_id}_comment_*')[-1]
    )
    if comments:
        comments = {
            'comments': [
                json.loads(comment.decode('utf-8')) for comment in comments
            ]
        }
    else:
        comments = {
            'comments': [
                db_obj_to_dict(comment)
                for comment in Comment.query.filter(
                    Comment.ticket_id == ticket_id
                ).all()
            ]
        }
    if isinstance(ticket, Ticket):
        return json.dumps(
            {**db_obj_to_dict(ticket), **comments},
            default=custom_encoder,
        )
    return json.dumps(
        {**json.loads(ticket), **comments}, default=custom_encoder
    )
