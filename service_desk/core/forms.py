from django import forms
from .models import Order


class PublicOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["category", "description", "address", "customer_name", "customer_contact"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        data = super().clean()
        if not data.get("customer_name") or not data.get("customer_contact"):
            raise forms.ValidationError("Укажите имя и контактные данные.")
        if not data.get("description"):
            raise forms.ValidationError("Опишите проблему.")
        return data


class OrderForm(forms.ModelForm):
    """
    Упрощённая форма создания/редактирования заявки,
    соответствующая описанию: category, description, address.
    """

    class Meta:
        model = Order
        fields = ["category", "description", "address"]


class AssignOrderForm(forms.Form):
    master_id = forms.IntegerField()
    planned_date = forms.DateTimeField(required=False, input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"])

