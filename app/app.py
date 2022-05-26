from datetime import datetime as dt

from flask import Response, json, request

from .db_models import Comment, Ticket, TicketStatus, db
from .helpers import (
    check_ticket_status,
    create_app,
    custom_encoder,
    db_obj_to_dict,
    get_ticket_response,
    redis_client,
)

app = create_app()


@app.route('/ticket', methods=['POST'])
def create_ticket():
    try:
        theme = request.form['theme']
        text = request.form['text']
        email = request.form['email']
    except:
        return Response(
            response=(
                '"theme", "text" and "email" is required as form-data strings.'
            ),
            status=400,
        )
    try:
        ticket = Ticket(theme=theme, text=text, email=email)
    except Exception as e:
        return Response(response=str(e), status=400)
    db.session.add(ticket)
    db.session.commit()
    db.session.refresh(ticket)
    json_ticket = json.dumps(db_obj_to_dict(ticket), default=custom_encoder)
    redis_client.set(
        f'ticket_{ticket.id}', json_ticket, ex=app.config['REDIS_EXPIRE_TIME']
    )
    return Response(
        response=get_ticket_response(ticket.id, redis_client),
        status=201,
        content_type='application/json',
    )


@app.route('/ticket/<int:ticket_id>', methods=['GET', 'PUT'])
def get_or_change_ticket(ticket_id):
    if request.method == 'GET':
        return Response(
            response=get_ticket_response(ticket_id, redis_client),
            status=200,
            content_type='application/json',
        )
    if request.method == 'PUT':
        ticket = Ticket.query.get_or_404(ticket_id)
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
            ticket.status = new_status
            ticket.updated_at = dt.utcnow()
            db.session.commit()
            db.session.refresh(ticket)
            json_ticket = json.dumps(
                db_obj_to_dict(ticket), default=custom_encoder
            )
            redis_client.set(
                f'ticket_{ticket.id}',
                json_ticket,
                ex=app.config['REDIS_EXPIRE_TIME'],
            )
            return Response(
                response=get_ticket_response(ticket_id, redis_client),
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
    return Response(
        response='Only GET and PUT methods is allowed.', status=405
    )


@app.route('/ticket/<int:ticket_id>/comment', methods=['POST'])
def create_comment(ticket_id):
    ticket = redis_client.get(f'ticket_{ticket_id}')
    if ticket:
        ticket_status = TicketStatus(json.loads(ticket)['status'])
    else:
        ticket = Ticket.query.get_or_404(ticket_id)
        ticket_status = ticket.status
    if ticket_status == TicketStatus.closed:
        return Response(response='Commenting closed tickets is unavailable.')
    try:
        text = request.form['text']
        email = request.form['email']
    except:
        return Response(
            response='"text" and "email" is required as form-data strings.',
            status=400,
        )
    try:
        comment = Comment(ticket_id=ticket_id, text=text, email=email)
    except Exception as e:
        return Response(response=str(e), status=400)
    db.session.add(comment)
    db.session.commit()
    db.session.refresh(comment)
    json_comment = json.dumps(db_obj_to_dict(comment), default=custom_encoder)
    # Подразумевается, что при удалении тикета, все комменты так же каскадно
    # удалятся из redis, как из бд, поэтому expire тут не задаём
    # это нужно и для правильной работы функции get_ticket_response
    redis_client.set(
        f'ticket_{comment.ticket_id}_comment_{comment.id}', json_comment
    )
    return Response(
        response=json_comment, status=201, content_type='application/json'
    )
