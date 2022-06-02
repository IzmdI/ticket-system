import unittest
from unittest.mock import patch

from fakeredis import FakeRedis

from app.db_crud import crud_comment, crud_ticket
from app.helpers import create_app
from app.views import bp, db


@patch('app.views.REDIS_CLIENT', FakeRedis())
class TestCase(unittest.TestCase):
    def setUp(self):
        app = create_app(for_tests=True)
        app.register_blueprint(bp)
        self.client = app.test_client()
        db.create_all()
        self.ticket = crud_ticket.create(
            db=db.session,
            theme='ticket theme',
            text='ticket text',
            email='email@email.email',
        )
        self.comment = crud_comment.create(
            db=db.session,
            text='comment text',
            email='email@email.email',
            ticket_id=1,
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_add_ticket(self):
        response = self.client.post(
            '/api/v1/ticket',
            data={
                'theme': 'test theme',
                'text': 'test text',
                'email': 'test@test.test',
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['id'], 2)
        self.assertEqual(response.json['theme'], 'test theme')
        self.assertEqual(response.json['text'], 'test text')
        self.assertEqual(response.json['email'], 'test@test.test')

    def test_email_validation(self):
        response = self.client.post(
            '/api/v1/ticket',
            data={
                'theme': 'test theme',
                'text': 'test text',
                'email': 'wrong email',
            },
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 400)

    def test_required_data_for_ticket(self):
        response = self.client.post(
            '/api/v1/ticket',
            data={
                'some': 'wrong',
            },
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 400)

    def test_get_ticket(self):
        response = self.client.get(f'api/v1/ticket/3')
        self.assertEqual(response.status_code, 404)
        response = self.client.get(f'api/v1/ticket/{self.ticket.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['theme'], 'ticket theme')
        self.assertEqual(response.json['text'], 'ticket text')
        self.assertEqual(response.json['email'], 'email@email.email')
        self.assertEqual(len(response.json['comments']), 1)

    def test_add_comment(self):
        response = self.client.post(
            f'api/v1/ticket/{self.ticket.id}/comment',
            data={'text': 'comment test text', 'email': 'comment@fake.test'},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['id'], 2)
        self.assertEqual(response.json['ticket_id'], 1)
        self.assertEqual(response.json['text'], 'comment test text')
        self.assertEqual(response.json['email'], 'comment@fake.test')

    def test_change_ticket_status(self):
        response = self.client.put(
            f'api/v1/ticket/{self.ticket.id}',
            data={'status': 'some wrong status'},
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.put(
            f'api/v1/ticket/{self.ticket.id}',
            data={'status': 'opened'},
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.put(
            f'api/v1/ticket/{self.ticket.id}',
            data={'status': 'awaited'},
        )
        self.assertEqual(response.status_code, 400)
        response = self.client.put(
            f'api/v1/ticket/{self.ticket.id}',
            data={'status': 'answered'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'answered')
        response = self.client.put(
            f'api/v1/ticket/{self.ticket.id}',
            data={'status': 'awaited'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'awaited')
        response = self.client.put(
            f'api/v1/ticket/{self.ticket.id}',
            data={'status': 'closed'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'closed')
        response = self.client.put(
            f'api/v1/ticket/{self.ticket.id}',
            data={'status': 'opened'},
        )
        self.assertEqual(response.status_code, 400)

    def test_add_comment_to_unexist_ticket(self):
        response = self.client.post(
            'api/v1/ticket/44/comment',
            data={'text': 'comment test text', 'email': 'comment@fake.test'},
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 404)

    def test_required_data_for_comment(self):
        self.client.post(
            '/api/v1/ticket',
            data={
                'theme': 'test theme',
                'text': 'test text',
                'email': 'test@test.test',
            },
        )
        response = self.client.post(
            'api/v1/ticket/2/comment',
            data={'some': 'error'},
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 400)

    def test_add_comment_to_closed_ticket(self):
        self.client.post(
            '/api/v1/ticket',
            data={
                'theme': 'test theme',
                'text': 'test text',
                'email': 'test@test.test',
            },
        )
        self.client.put(
            'api/v1/ticket/2',
            data={'status': 'closed'},
        )
        response = self.client.post(
            'api/v1/ticket/2/comment',
            data={'text': 'comment test text', 'email': 'comment@fake.test'},
        )
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 400)


def tests():
    unittest.main()


if __name__ == '__main__':
    tests()
