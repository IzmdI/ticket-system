import json
import re
from typing import Optional, Union

from redis import Redis
from sqlalchemy.orm import Session

from app.db_models import Comment, Ticket, db
from app.db_schemas import CommentSchema, TicketSchema
from app.helpers import get_redis_client

Model = Union[Ticket, Comment]
Schema = Union[TicketSchema, CommentSchema]


class BaseUtils:
    def __init__(self, model: Model, schema: Schema):
        self.model = model
        self.schema = schema

    def create_db_obj(self, db: Session, **kwargs) -> Model:
        if kwargs.get('email') is not None:
            kwargs['email'] = self.email_validator(kwargs['email'])
        obj = self.model(**kwargs)  # noqa
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def get_db_obj(self, db: Session, obj_id: int) -> Optional[Model]:
        return db.query(self.model).filter(self.model.id == obj_id).first()

    @staticmethod
    def update_db_obj(db: Session, obj: Model, **kwargs) -> Model:
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    def remove_db_obj(
        self, db: Session, obj_id: int, redis_client: Redis, match_str: str
    ) -> int:
        obj = self.get_db_obj(obj_id=obj_id)
        db.delete(obj)
        db.commit()
        redis_client.delete(*redis_client.scan(match=match_str)[-1])
        return obj.id

    @staticmethod
    def email_validator(email):
        if not email or not re.match(
            r'^[A-Za-z0-9.+_-]+@[A-Za-z0-9._-]+\.[a-zA-Z]*$', email
        ):
            raise AssertionError(
                'Provided value is not a valid e-mail address.'
            )
        return email

    def as_dict(self, **kwargs) -> dict:
        obj = kwargs.get('obj')
        if obj:
            return self.schema.dump(obj)
        pass


class TicketUtils(BaseUtils):
    def as_dict(self, **kwargs) -> dict:
        obj = kwargs.get('obj')
        ticket_id = kwargs.get('ticket_id')
        if obj:
            return self.schema.dump(obj)
        redis_client = get_redis_client()
        ticket = redis_client.get(f'ticket_{ticket_id}')
        if not ticket:
            redis_client.close()
            ticket = self.get_db_obj(db=db.session, obj_id=ticket_id)
            if not ticket:
                return {}
            return self.schema.dump(ticket)
        comments = redis_client.mget(
            redis_client.scan(match=f'ticket_{ticket_id}_comment_*')[-1]
        )
        redis_client.close()
        comments = {'comments': [json.loads(comment) for comment in comments]}
        return {**json.loads(ticket), **comments}  # noqa


ticket_utils = TicketUtils(Ticket, TicketSchema())  # noqa
comment_utils = BaseUtils(Comment, CommentSchema())  # noqa
