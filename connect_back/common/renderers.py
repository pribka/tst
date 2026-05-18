from rest_framework.renderers import BrowsableAPIRenderer


class NoFormBrowsableAPIRenderer(BrowsableAPIRenderer):
    def get_rendered_html_form(self, data, view, method, request):
        """
        Возвращаем None, чтобы HTML-форма не рендерилась.
        Это именно то место, где DRF обычно делает запросы к БД.
        """
        return None

