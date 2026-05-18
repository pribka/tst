from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from common.views import BaseCatalogViewSet
from users.models import ProfileModel

from . import models
from . import serializers


class FlowchartApiViewSet(BaseCatalogViewSet):
    model = models.FlowchartModel

    def get_queryset(self):
        return self.model.get_queryset()
