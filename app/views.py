import os

from flask import Blueprint, request

from app import handlers
from app.db_models import db

bp = Blueprint('api', __name__, url_prefix="/api/v1")
# bp = Blueprint('api', __name__, url_prefix=f"/api/{os.environ['API_VERSION']}")


@bp.route('/ticket', methods=['POST'])
def create_ticket():
    return handlers.create_new_ticket(request)


@bp.route('/ticket/<int:ticket_id>', methods=['GET'])
def get_ticket(ticket_id):
    return handlers.get_ticket(ticket_id)


@bp.route('/ticket/<int:ticket_id>', methods=['PUT'])
def change_ticket_status(ticket_id):
    return handlers.update_ticket_status(request, ticket_id)


@bp.route('/ticket/<int:ticket_id>/comment', methods=['POST'])
def create_comment(ticket_id):
    return handlers.add_comment(request, ticket_id)


if __name__ == '__main__':
    from app.helpers import create_app, get_redis_client

    try:
        redis_client = get_redis_client()
        redis_client.ping()
        redis_client.close()
    except Exception:
        raise
    try:
        app = create_app()
        app.register_blueprint(bp)
        app.run(host='0.0.0.0', port=8000)
    except Exception:
        raise
    finally:
        redis_client.flushdb()
        redis_client.close()
        db.drop_all()
