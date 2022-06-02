from app.helpers import create_app
from app.views import REDIS_CLIENT, bp
from app.tests import tests

app = create_app()
app.register_blueprint(bp)


if __name__ == '__main__':
    try:
        tests()
        app.run()
    except:
        pass
    finally:
        REDIS_CLIENT.flushdb()
        REDIS_CLIENT.close()
