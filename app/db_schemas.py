from marshmallow_enum import EnumField
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from marshmallow_sqlalchemy.fields import Nested

from app.db_models import Comment, Ticket, TicketStatus


class CommentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Comment

    ticket_id = auto_field()


class TicketSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Ticket
        include_relationships = True
        load_instance = True

    status = EnumField(TicketStatus)
    comments = Nested(CommentSchema, many=True)  # noqa


ticket_schema = TicketSchema()
comment_schema = CommentSchema()
