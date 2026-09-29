from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Profile(models.Model):
    ROLE_CHOICES = [("teacher", "Преподаватель"), ("trainee", "Диспетчер ДДС")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile", verbose_name="Пользователь")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="trainee", verbose_name="Роль")
    group_name = models.CharField(max_length=120, blank=True, verbose_name="Учебная группа")
    position = models.CharField(max_length=180, blank=True, verbose_name="Должность")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Телефон")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Scenario(models.Model):
    DIFFICULTY_CHOICES = [(1, "Базовая"), (2, "Средняя"), (3, "Повышенная")]
    title = models.CharField(max_length=200, verbose_name="Название учебной карточки")
    category = models.CharField(max_length=160, verbose_name="Тип происшествия")
    classifier_code = models.CharField(max_length=30, blank=True, verbose_name="Код классификатора")
    difficulty = models.PositiveSmallIntegerField(choices=DIFFICULTY_CHOICES, default=1, verbose_name="Сложность")
    time_limit = models.PositiveIntegerField(default=180, verbose_name="Норматив первой записи, сек")
    reaction_limit = models.PositiveIntegerField(default=30, verbose_name="Норматив открытия карточки, сек")
    description = models.TextField(blank=True, verbose_name="Описание учебной ситуации")
    caller_name = models.CharField(max_length=120, default="Заявитель", verbose_name="Источник сообщения")
    caller_phone = models.CharField(max_length=30, default="", blank=True, verbose_name="Телефон источника")
    initial_message = models.TextField(blank=True, verbose_name="Сообщение для ДДС")
    dialogue = models.JSONField(default=list, blank=True, verbose_name="Служебный диалог")
    expected = models.JSONField(default=dict, blank=True, verbose_name="Эталон карточки")
    services = models.JSONField(default=list, blank=True, verbose_name="Получатели карточки")
    fields = models.JSONField(default=list, blank=True, verbose_name="Поля карточки")
    response_algorithm = models.JSONField(default=list, blank=True, verbose_name="Алгоритм реагирования")
    service_contacts = models.JSONField(default=list, blank=True, verbose_name="Руководители реагирующих служб")
    ai_generated = models.BooleanField(default=False, verbose_name="Сформировано системой")
    approved = models.BooleanField(default=True, verbose_name="Утверждено преподавателем")
    source_code = models.CharField(max_length=60, blank=True, verbose_name="Источник данных")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_scenarios", verbose_name="Автор")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Изменено")

    class Meta:
        ordering = ["category", "title"]
        verbose_name = "Учебная карточка"
        verbose_name_plural = "Учебные карточки"

    def __str__(self):
        return f"{self.title} [{self.get_difficulty_display()}]"

class Assignment(models.Model):
    STATUS_CHOICES = [("new", "Назначено"), ("active", "В работе"), ("done", "Завершено")]
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT, related_name="assignments", verbose_name="Учебная карточка")
    trainee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assignments", verbose_name="Диспетчер ДДС")
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="issued_assignments", verbose_name="Преподаватель")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new", verbose_name="Статус")
    due_at = models.DateTimeField(null=True, blank=True, verbose_name="Срок выполнения")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Назначено")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Назначение"
        verbose_name_plural = "Назначения"

    def __str__(self):
        return f"{self.trainee} — {self.scenario}"

class Attempt(models.Model):
    STATUS_CHOICES = [("active", "В работе"), ("finished", "Завершено"), ("expired", "Время истекло")]
    assignment = models.ForeignKey(Assignment, on_delete=models.PROTECT, related_name="attempts", verbose_name="Назначение")
    trainee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attempts", verbose_name="Диспетчер ДДС")
    started_at = models.DateTimeField(default=timezone.now, verbose_name="Начало занятия")
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="Открытие карточки")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Завершение")
    reaction_time = models.FloatField(default=0, verbose_name="Время открытия")
    fill_time = models.FloatField(default=0, verbose_name="Время первой записи")
    score = models.PositiveSmallIntegerField(default=0, verbose_name="Оценка")
    grammar_score = models.PositiveSmallIntegerField(default=100, verbose_name="Грамматика")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", verbose_name="Статус")
    errors = models.JSONField(default=list, blank=True, verbose_name="Замечания")
    ai_feedback = models.TextField(blank=True, verbose_name="Анализ системы")
    teacher_feedback = models.TextField(blank=True, verbose_name="Комментарий преподавателя")
    transcript = models.JSONField(default=list, blank=True, verbose_name="Протокол связи")
    first_record_at = models.DateTimeField(null=True, blank=True, verbose_name="Первая запись")

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "Занятие"
        verbose_name_plural = "Занятия"

    def __str__(self):
        return f"{self.trainee} — {self.assignment.scenario.title} — {self.score}"

class IncidentCard(models.Model):
    attempt = models.OneToOneField(Attempt, on_delete=models.CASCADE, related_name="card", verbose_name="Занятие")
    incident_number = models.CharField(max_length=30, blank=True, verbose_name="Номер карточки")
    event_type = models.CharField(max_length=200, blank=True, verbose_name="Тип происшествия")
    address = models.CharField(max_length=300, blank=True, verbose_name="Адрес")
    details = models.TextField(blank=True, verbose_name="Обстоятельства")
    apartment = models.CharField(max_length=30, blank=True, verbose_name="Квартира")
    entrance = models.CharField(max_length=30, blank=True, verbose_name="Подъезд")
    floor = models.CharField(max_length=30, blank=True, verbose_name="Этаж")
    people_inside = models.CharField(max_length=30, blank=True, verbose_name="Люди на месте")
    children = models.CharField(max_length=30, blank=True, verbose_name="Дети")
    injured = models.CharField(max_length=30, blank=True, verbose_name="Пострадавшие")
    open_fire = models.CharField(max_length=30, blank=True, verbose_name="Открытое пламя")
    receiving_departments = models.JSONField(default=list, blank=True, verbose_name="ДДС-получатели")
    services = models.JSONField(default=list, blank=True, verbose_name="Службы")
    operator_note = models.TextField(blank=True, verbose_name="Комментарий диспетчера")
    validation_note = models.TextField(blank=True, verbose_name="Замечание по карточке")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Изменено")

    def __str__(self):
        return f"Карточка {self.incident_number or self.attempt_id}"

class CardStatus(models.Model):
    STATUS_CHOICES = [
        ("accepted", "Принято"),
        ("not_accepted", "Не принято"),
        ("response_started", "Начало реагирования"),
        ("arrived", "Прибытие"),
        ("work", "Проведение работ"),
        ("completed", "Завершение"),
        ("refused", "Отказ"),
    ]
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="status_records", verbose_name="Занятие")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, verbose_name="Статус карточки")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Автор")

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Статус карточки"
        verbose_name_plural = "Статусы карточек"

    def __str__(self):
        return f"{self.get_status_display()} — {self.attempt_id}"

class AttemptEvent(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="events", verbose_name="Занятие")
    event_type = models.CharField(max_length=60, verbose_name="Событие")
    payload = models.JSONField(default=dict, blank=True, verbose_name="Данные")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время")

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Событие занятия"
        verbose_name_plural = "События занятий"

class TeacherCorrection(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name="corrections", verbose_name="Учебная карточка")
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Преподаватель")
    correction = models.TextField(verbose_name="Поправка преподавателя")
    applied = models.BooleanField(default=True, verbose_name="Учитывать при генерации")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Поправка преподавателя"
        verbose_name_plural = "Поправки преподавателей"

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Пользователь")
    action = models.CharField(max_length=180, verbose_name="Действие")
    object_type = models.CharField(max_length=80, blank=True, verbose_name="Тип объекта")
    object_id = models.CharField(max_length=80, blank=True, verbose_name="Идентификатор")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP-адрес")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Журнал действий"
        verbose_name_plural = "Журнал действий"

    def __str__(self):
        return f"{self.created_at:%d.%m.%Y %H:%M:%S} — {self.action}"
