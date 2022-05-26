from app.app import app, redis_client

if __name__ == '__main__':
    try:
        app.run()
    finally:
        redis_client.close()
