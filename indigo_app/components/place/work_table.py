from django import forms
from django.core.paginator import Paginator, InvalidPage
from django_unicorn.components import UnicornView

from indigo_api.models import Work


class WorkFilterForm(forms.Form):
    q = forms.CharField(required=False)
    page = forms.IntegerField(required=False)
    primary_subsidiary = forms.ChoiceField(required=False)
    order = forms.CharField(required=False)


class WorkTableView(UnicornView):
    _per_page = 15
    _qs = Work.objects
    form_class = WorkFilterForm

    q = ""
    page = 1
    primary_subsidiary = "b"
    order = "title"
    selected = []

    def toggle(self, pk):
        if pk in self.selected:
            self.selected = [x for x in self.selected if x != pk]
        else:
            self.selected.append(pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        works = self.filter_queryset(self._qs)
        context["paginator"], context["page"] = self.paginate(works.all())

        return context

    def filter_queryset(self, qs):
        qs = qs.order_by(self.order)

        if self.q:
            qs = qs.filter(title__icontains=self.q)

        if self.primary_subsidiary == "p":
            qs = qs.filter(parent_work__isnull=True)
        elif self.primary_subsidiary == "s":
            qs = qs.filter(parent_work__isnull=False)

        return qs

    def paginate(self, object_list):
        paginator = Paginator(object_list, self._per_page)
        page = self.page or 1

        try:
            page_number = int(page)
        except ValueError:
            if page == 'last':
                page_number = paginator.num_pages
            else:
                page_number = 1

        try:
            page = paginator.page(page_number)
            return paginator, page
        except InvalidPage:
            return paginator, None
