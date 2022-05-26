# Ticket system

This is a simple API service, which allows to send tickets, update them statuses and comments them.  
By default ticket creating with status 'opened'.  
* Opened ticket can be 'answered' or 'closed'. 
* Answered ticket can be 'awaited' or 'closed'. 
* Awaited ticket can be 'answered' or 'closed'. 
* Closed ticket can't be changed. 
* Only not closed tickets can be commented.

## Before Started

You will need [Docker](https://docs.docker.com/get-docker/) to run it. Install last version depending from your OS. After installation just clone this repository.

### Starting

First, open a `.env.example` file, set some variables and save it as `.env` without `.example` extension.  
IMPORTANT: Make your own unique secret variables.

```
# Application secret key
SECRET_KEY=<YOUR_SECRET_KEY>
# Database config
POSTGRES_USER=system_admin  //set own
POSTGRES_PASSWORD=<YOUR_DB_PASSWORD>
POSTGRES_DB=tickets  //set own
# Redis config
REDIS_URL=redis://redis-service
REDIS_USER=default
REDIS_PASSWORD=<YOUR_REDIS_PASSWORD>
REDIS_EXPIRE_TIME=60  // set time for Redis TTL in seconds
```

Start building and setting up.

```
docker-compose up
```

Service will accessible locally at 8000 port.

```
localhost:8000
```

The following endpoints are available.  
* `/ticket`  
    * POST - create ticket
        * Required form-data:
           * theme: string
           * text: string
           * email: string
* `/ticket/ticket_id`
    * Required query param:
        * ticket_id: int
    * GET - get ticket
    * PUT - update ticket status
        * Required form-data:
           * status: string  
           Valid only: "answered", "awaited", "closed"
* `/ticket/ticket_id/comment` 
    * Required query param:
        * ticket_id: int 
    * POST - add commentary to ticket
        * Required form-data:
           * text: string
           * email: string

## Built With

* [Flask](https://palletsprojects.com/p/flask/) - lightweight WSGI web application framework
* [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/) - extension for Flask that adds support for [SQLAlchemy](https://www.sqlalchemy.org/)
* [Redis](https://redis.io/) - in-memory data storage and message broker
* [uWSGI](https://uwsgi-docs.readthedocs.io/en/latest/) - service for web-applications hosting
* [Docker](https://www.docker.com/) - Containerized system

## Author

* **[Andrew Smelov](https://github.com/IzmdI)**

## License

This project is licensed under the MIT License - see the LICENSE.md file for details