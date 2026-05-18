from django.forms import BaseInlineFormSet, ModelForm
from dal import autocomplete

from . import models
from common.catalogs.models import NomenclatureModel
from django import forms
from django.urls import reverse_lazy


class HelpDeskCostForm(ModelForm):
    class Meta:
        model = models.HelpDeskCostModel
        fields = ('goods', 'quantity',)
        widgets = {
            'goods': autocomplete.ModelSelect2(url=reverse_lazy('catalogs:nomenclatures-autocomplete'), attrs={'required': 'required'}),
        }

    def __init__(self, *args, **kwargs):
        # Извлекаем родительский объект (instance) из kwargs перед super().__init__
        # Родительский объект передается как 'instance' в формах инлайн-формсета,
        # когда они уже сохранены.
        # Но при инициализации всего формсета, нам нужно поймать его раньше.

        # Если вы передадите extra_context={'parent_instance': Ticket} в formset_factory,
        # вы сможете поймать его здесь.
        self.ticket_instance = kwargs.pop('ticket_instance', None)
        super().__init__(*args, **kwargs)
        if 'goods' in self.fields:
            # Устанавливаем required=True явно (если в модели allow null)
            self.fields['goods'].required = True
            # Исключаем пустой вариант выбора из списка
            self.fields['goods'].empty_label = None
            url = reverse_lazy('catalogs:nomenclatures-autocomplete')
            contractor_id = self.ticket_instance.customer_card.org_admin.pk
            self.fields['goods'].widget.url = f"{url}?contractor={contractor_id}"
        if 'quantity' in self.fields:
            if not self.instance.pk:
                self.fields['quantity'].initial = 1
            self.fields['quantity'].widget.attrs['min'] = '0.001'
        # если форма привязана к существующей дочерней модели.
        if self.ticket_instance:
            # Фильтруем QuerySet для поля 'goods'
            ticket_instance = self.ticket_instance
            self.fields['goods'].queryset = NomenclatureModel.objects.filter(
                is_active=True,
                contractor=ticket_instance.customer_card.org_admin
            )
        else:
            # Если это пустая форма (новая запись) или форма без привязки,
            # мы пока не знаем, что фильтровать.
            # Мы можем оставить пустой queryset или отфильтровать по общим правилам.
            self.fields['goods'].queryset = NomenclatureModel.objects.none()
            # Или: self.fields['goods'].queryset = NomenklaturaModel.objects.filter(is_active=True)

    def clean_goods(self):
        # Валидация поля goods
        # Получаем очищенное значение поля goods (это будет объект NomenklatureModel)
        goods_instance = self.cleaned_data.get('goods')

        # Получаем родительский объект тикета, который мы сохранили в __init__
        ticket = self.ticket_instance

        # Выполняем проверку, только если оба объекта существуют
        if goods_instance and ticket:
            # Валидация:
            if not ticket.customer_card.org_admin == goods_instance.contractor:
                raise forms.ValidationError(
                    "Этот товар не соответствует организации техподдержки, указанной в обращении. "
                    "Выберите другой товар.",
                    code='invalid_goods',
                    params={'goods': goods_instance},
                )
        # Всегда возвращаем очищенные данные в конце метода
        return goods_instance
