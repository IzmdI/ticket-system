from app.helpers import create_app
from app.views import bp
from app.tests import tests

app = create_app()
app.register_blueprint(bp)


if __name__ == '__main__':
    try:
        tests()
        app.run()
    except Exception:
        raise
