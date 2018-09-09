from django.http import HttpResponse

from django.views.generic import TemplateView


class ProfileView(TemplateView):
    template_name = 'profile.html'
    def profile(self):
        return HttpResponse("hI tHiS iS mY pRoFiLe")
