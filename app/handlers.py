import os
from datetime import datetime as dt
import json
from typing import Tuple

from flask import Request, abort

from app.db_crud import crud_comment, crud_ticket
from app.db_models import TicketStatus, db
from app.helpers import (
    check_ticket_status,
    get_comment_as_dict,
    get_redis_client,
    get_ticket_as_dict,
)


expire_time = 30
# expire_time = int(os.environ['REDIS_EXPIRE_TIME'])


def create_new_ticket(request: Request) -> Tuple[dict, int]:
    try:
        theme = request.json['theme']
        text = request.json['text']
        email = request.json['email']
        ticket = crud_ticket.create(
            db=db.session, theme=theme, text=text, email=email
        )
    except KeyError as e:
        return {'error': f'{str(e)} is required.'}, 400
    except Exception as e:
        return {'error': str(e)}, 400
    ticket = get_ticket_as_dict(ticket.id, ticket)
    redis_client = get_redis_client()
    redis_client.set(
        f'ticket_{ticket["id"]}', json.dumps(ticket), ex=expire_time
    )
    redis_client.close()
    return ticket, 201


def get_ticket(ticket_id: int) -> Tuple[dict, int]:
    ticket = get_ticket_as_dict(ticket_id)
    if not ticket:
        return abort(404)
    return ticket, 200


def update_ticket_status(request: Request, ticket_id: int) -> Tuple[dict, int]:
    ticket = crud_ticket.get(obj_id=ticket_id)
    if not ticket:
        return abort(404)
    if ticket.status == TicketStatus.closed:
        return {'error': 'closed ticket can\'t be changed.'}, 400
    try:
        new_status = TicketStatus(request.json['status'])
    except KeyError as e:
        return {'error': f'{str(e)} is required.'}, 400
    except ValueError:
        return {
            'error': (
                f'{request.json["status"]} is not a valid status.',
                ' Valid only: "answered", "awaited", "closed".',
                ' Opened ticket can only be answered or closed.',
                ' Answered ticket can only be awaited or closed',
                ' Awaited ticket can only be answered or closed.',
            )
        }, 400
    if check_ticket_status(ticket.status, new_status):
        upd_ticket = crud_ticket.update(
            db=db.session,
            obj=ticket,
            status=new_status,
            updated_at=dt.utcnow(),
        )
        ticket = get_ticket_as_dict(ticket_id, upd_ticket)
        redis_client = get_redis_client()
        redis_client.set(
            f'ticket_{ticket["id"]}',
            json.dumps(ticket),
            ex=expire_time,
        )
        redis_client.close()
        return ticket, 200
    return {
        'error': (
            f'{new_status.name} can\'t be assign ',
            f'to {ticket.status.name} ticket.',
        )
    }, 400


def add_comment(request: Request, ticket_id: int) -> Tuple[dict, int]:
    redis_client = get_redis_client()
    ticket = redis_client.get(f'ticket_{ticket_id}')
    redis_client.close()
    if ticket:
        ticket_status = TicketStatus(json.loads(ticket)['status'])
    else:
        ticket = crud_ticket.get(db=db.session, obj_id=ticket_id)
        if not ticket:
            return abort(404)
        ticket_status = ticket.status
    if ticket_status == TicketStatus.closed:
        return {'error': 'commenting closed tickets is unavailable.'}, 400
    try:
        text = request.json['text']
        email = request.json['email']
        comment = crud_comment.create(
            db=db.session, ticket_id=ticket_id, text=text, email=email
        )
    except KeyError as e:
        return {'error': f'{str(e)} is required.'}, 400
    except Exception as e:
        return {'error': str(e)}, 400
    comment = get_comment_as_dict(comment)
    redis_client = get_redis_client()
    redis_client.set(
        f'ticket_{comment["ticket_id"]}_comment_{comment["id"]}',
        json.dumps(comment),
    )
    redis_client.close()
    return comment, 201
