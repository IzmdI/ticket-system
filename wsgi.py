from app.helpers import create_app
from app.tests import tests
from app.views import bp


app = create_app()
app.register_blueprint(bp)


if __name__ == '__main__':
    try:
        tests()
        app.run()
    except Exception:
        raise
