import os
from datetime import datetime as dt

from flask import Blueprint, Response, json, request

from app.db_crud import crud_comment, crud_ticket
from app.db_models import TicketStatus, db
from app.helpers import (
    check_ticket_status,
    get_comment_json,
    get_redis_client,
    get_ticket_json,
)

bp = Blueprint('api', __name__, url_prefix="/api/v1")
# bp = Blueprint('api', __name__, url_prefix=f"/api/{os.environ['API_VERSION']}")
expire_time = 30
# expire_time = int(os.environ['REDIS_EXPIRE_TIME'])


@bp.route('/ticket', methods=['POST'])
def create_ticket():
    try:
        theme = request.json['theme']
        text = request.json['text']
        email = request.json['email']
    except:
        return Response(
            response=(
                '"theme", "text" and "email" is required as json-data strings.'
            ),
            status=400,
        )
    try:
        ticket = crud_ticket.create(
            db=db.session, theme=theme, text=text, email=email
        )
    except Exception as e:
        return Response(response=str(e), status=400)
    redis_client = get_redis_client()
    json_ticket = get_ticket_json(ticket.id, redis_client, ticket)
    redis_client.set(f'ticket_{ticket.id}', json_ticket, ex=expire_time)
    redis_client.close()
    return Response(
        response=json_ticket,
        status=201,
        content_type='application/json',
    )


@bp.route('/ticket/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    redis_client = get_redis_client()
    return Response(
        response=get_ticket_json(ticket_id, redis_client),
        status=200,
        content_type='application/json',
    )


@bp.route('/ticket/<int:ticket_id>', methods=['PUT'])
def change_ticket_status(ticket_id):
    ticket = crud_ticket.get(obj_id=ticket_id)
    if ticket.status == TicketStatus.closed:
        return Response(
            response='Closed ticket can\'t be changed.', status=400
        )
    try:
        new_status = TicketStatus(request.form['status'])
    except ValueError:
        return Response(
            response=(
                f'{request.form["status"]} is not a valid status.',
                ' Valid only: "answered", "awaited", "closed".',
                ' Opened ticket can only be answered or closed.',
                ' Answered ticket can only be awaited or closed',
                ' Awaited ticket can only be answered or closed.',
            ),
            status=400,
        )
    if check_ticket_status(ticket.status, new_status):
        upd_ticket = crud_ticket.update(
            db=db.session,
            obj=ticket,
            status=new_status,
            updated_at=dt.utcnow(),
        )
        redis_client = get_redis_client()
        json_ticket = get_ticket_json(ticket_id, redis_client, upd_ticket)
        redis_client.set(
            f'ticket_{ticket.id}',
            json_ticket,
            ex=expire_time,
        )
        redis_client.close()
        return Response(
            response=json_ticket,
            status=200,
            content_type='application/json',
        )
    return Response(
        response=(
            f'{new_status.name} can\'t be assign ',
            f'to {ticket.status.name} ticket.',
        ),
        status=400,
    )


@bp.route('/ticket/<int:ticket_id>/comment', methods=['POST'])
def create_comment(ticket_id):
    redis_client = get_redis_client()
    ticket = redis_client.get(f'ticket_{ticket_id}')
    if ticket:
        ticket_status = TicketStatus(json.loads(ticket)['status'])
    else:
        ticket = crud_ticket.get(obj_id=ticket_id)
        ticket_status = ticket.status
    if ticket_status == TicketStatus.closed:
        return Response(
            response='Commenting closed tickets is unavailable.', status=400
        )
    try:
        text = request.json['text']
        email = request.json['email']
    except:
        return Response(
            response='"text" and "email" is required as json-data strings.',
            status=400,
        )
    try:
        comment = crud_comment.create(
            db=db.session, ticket_id=ticket_id, text=text, email=email
        )
    except Exception as e:
        return Response(response=str(e), status=400)
    json_comment = get_comment_json(comment)
    redis_client = get_redis_client()
    redis_client.set(
        f'ticket_{comment.ticket_id}_comment_{comment.id}', json_comment
    )
    redis_client.close()
    return Response(
        response=json_comment, status=201, content_type='application/json'
    )


if __name__ == '__main__':
    from app.helpers import create_app

    try:
        redis_client = get_redis_client()
        redis_client.ping()
        redis_client.close()
    except:
        raise
    try:
        app = create_app()
        app.register_blueprint(bp)
        app.run(host='0.0.0.0', port=8000)
    except:
        raise
    finally:
        redis_client.flushdb()
        redis_client.close()
        db.drop_all()
