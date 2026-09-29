from django import forms
from django.contrib.auth.models import User
from .models import Assignment, IncidentCard, Scenario

class ScenarioForm(forms.ModelForm):
    class Meta:
        model = Scenario
        fields = [
            "title", "category", "classifier_code", "difficulty", "time_limit",
            "reaction_limit", "description", "initial_message", "expected",
            "services", "fields", "response_algorithm", "service_contacts", "approved"
        ]
        labels = {
            "title": "Название учебной карточки",
            "category": "Тип происшествия",
            "classifier_code": "Код классификатора",
            "difficulty": "Сложность",
            "time_limit": "Норматив первой записи, секунд",
            "reaction_limit": "Норматив открытия карточки, секунд",
            "description": "Описание учебной ситуации",
            "initial_message": "Сообщение для ДДС",
            "expected": "Эталон карточки",
            "services": "ДДС-получатели",
            "fields": "Поля карточки",
            "response_algorithm": "Алгоритм реагирования",
            "service_contacts": "Руководители реагирующих служб",
            "approved": "Утверждено преподавателем",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "initial_message": forms.Textarea(attrs={"rows": 4}),
            "expected": forms.Textarea(attrs={"rows": 10}),
            "services": forms.Textarea(attrs={"rows": 5}),
            "fields": forms.Textarea(attrs={"rows": 5}),
            "response_algorithm": forms.Textarea(attrs={"rows": 7}),
            "service_contacts": forms.Textarea(attrs={"rows": 5}),
        }

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ["scenario", "trainee", "due_at"]
        labels = {"scenario": "Учебная карточка", "trainee": "Диспетчер ДДС", "due_at": "Срок выполнения"}
        widgets = {"due_at": forms.DateTimeInput(attrs={"type": "datetime-local"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["trainee"].queryset = User.objects.filter(profile__role="trainee", is_active=True)
        self.fields["scenario"].queryset = Scenario.objects.filter(approved=True)

class IncidentCardForm(forms.ModelForm):
    class Meta:
        model = IncidentCard
        fields = ["validation_note", "operator_note"]
        labels = {"validation_note": "Замечание по данным карточки", "operator_note": "Комментарий диспетчера"}
        widgets = {"validation_note": forms.Textarea(attrs={"rows": 3}), "operator_note": forms.Textarea(attrs={"rows": 3})}
