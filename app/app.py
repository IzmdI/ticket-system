from datetime import datetime as dt
from enum import Enum

from flask import Flask, Response, json, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config[
    'SQLALCHEMY_DATABASE_URI'
] = 'postgresql://postgres:postgres@localhost:5432/tickets'
db = SQLAlchemy(app)


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


def db_obj_to_dict(obj: db.Model) -> dict:
    return {
        column.name: getattr(obj, column.name)
        for column in obj.__table__.columns
    }


def custom_encoder(obj):
    if isinstance(obj, dt):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.name


def check_ticket_status(ticket: Ticket, new_status: TicketStatus) -> bool:
    return (
        ticket.status == TicketStatus.opened
        or ticket.status == TicketStatus.awaited
        and new_status in (TicketStatus.answered, TicketStatus.closed)
        or ticket.status == TicketStatus.answered
        and new_status in (TicketStatus.awaited, TicketStatus.closed)
    )


@app.route('/ticket', methods=['POST'])
def create_ticket():
    ticket = Ticket(
        theme=request.form['theme'],
        text=request.form['text'],
        email=request.form['email'],
    )
    db.session.add(ticket)
    db.session.commit()
    db.session.refresh(ticket)
    return Response(
        response=json.dumps(db_obj_to_dict(ticket), default=custom_encoder),
        status=201,
        content_type='application/json',
    )


@app.route('/ticket/<int:ticket_id>', methods=['GET', 'PUT'])
def get_or_change_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    comments = {
        'comments': [db_obj_to_dict(comment) for comment in ticket.comments]
    }
    if request.method == 'GET':
        return Response(
            response=json.dumps(
                {**db_obj_to_dict(ticket), **comments}, default=custom_encoder
            ),
            status=200,
            content_type='application/json',
        )
    if request.method == 'PUT':
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
        if check_ticket_status(ticket, new_status):
            ticket.status = new_status
            ticket.updated_at = dt.utcnow()
            db.session.commit()
            db.session.refresh(ticket)
            return Response(
                response=json.dumps(
                    db_obj_to_dict(ticket), default=custom_encoder
                ),
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
    ticket = Ticket.query.get_or_404(ticket_id)
    comment = Comment(
        ticket_id=ticket.id,
        text=request.form['text'],
        email=request.form['email'],
    )
    db.session.add(comment)
    db.session.commit()
    db.session.refresh(comment)
    return Response(
        response=json.dumps(db_obj_to_dict(comment), default=custom_encoder),
        status=201,
        content_type='application/json',
    )


if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=8000)
