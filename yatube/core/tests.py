from http import HTTPStatus

from django.test import TestCase


class ViewTestClass(TestCase):

    def test_error_page(self):
        """При запросе несуществующей страницы сервер возвращает код 404,
        с соответствующим шаблоном.
        """
        url_names = (
            ('/nonexist-page/', 'core/404.html'),
        )
        for url, template in url_names:
            with self.subTest():
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
                self.assertTemplateUsed(response, template)

