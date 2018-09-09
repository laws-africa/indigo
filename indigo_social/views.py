from __future__ import unicode_literals

from django.shortcuts import render

from django.http import HttpResponse


def profile(request):
    return HttpResponse("hI tHiS iS mY pRoFiLe")
