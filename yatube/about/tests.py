from http import HTTPStatus

from django.test import TestCase, Client


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_urls_exists_at_desired_locations(self):
        url_names = (
                '/about/author/',
                '/about/tech/'
        )
        for address in url_names:
            with self.subTest():
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404(self):
        """При запросе несуществующей страницы сервер возвращает код 404."""
        response = self.guest_client.get('/about/тест/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)