from app.app import REDIS_CLIENT, app

if __name__ == '__main__':
    try:
        app.run()
    finally:
        REDIS_CLIENT.close()
