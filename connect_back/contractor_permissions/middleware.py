from django.core.exceptions import PermissionDenied
from django.http import JsonResponse

from common.utils import use_access_groups, get_available_section_codes

from .utils import get_section_codes_by_slug


class ContractorPermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        profile = getattr(request.user, 'profile', None)
        if profile:
            profile_id = profile.pk
            if use_access_groups(profile_id):
                path = request.path
                path_list = path.split('/')
                try:
                    slug = path_list[3]
                except IndexError:
                    pass
                else:
                    section_codes = get_section_codes_by_slug(slug)
                    if section_codes:
                        available_section_codes = set(get_available_section_codes(request.user.profile))
                        if section_codes.isdisjoint(available_section_codes):
                            return JsonResponse({"detail": "Раздел недоступен"}, status=403)
        response = self.get_response(request)
        return response

