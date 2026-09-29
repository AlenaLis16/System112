import json
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .ai_service import evaluate_attempt, generate_scenario, generate_service_reply
from .forms import AssignmentForm, ScenarioForm
from .models import Assignment, Attempt, AttemptEvent, AuditLog, CardStatus, IncidentCard, Scenario, TeacherCorrection


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            if request.user.is_superuser:
                return view(request, *args, **kwargs)
            if not hasattr(request.user, "profile") or request.user.profile.role != role:
                return HttpResponseForbidden("Доступ запрещён")
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def audit(request, action, object_type="", object_id=""):
    AuditLog.objects.create(user=request.user, action=action, object_type=object_type, object_id=str(object_id), ip_address=request.META.get("REMOTE_ADDR"))


def home(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if request.user.is_superuser or (hasattr(request.user, "profile") and request.user.profile.role == "teacher"):
        return redirect("teacher_dashboard")
    return redirect("trainee_dashboard")


@login_required
@role_required("teacher")
def teacher_dashboard(request):
    assignments = Assignment.objects.select_related("scenario", "trainee").all()[:12]
    scenarios = Scenario.objects.all()[:12]
    attempts = Attempt.objects.select_related("assignment__scenario", "trainee").all()[:12]
    avg_score = Attempt.objects.filter(status="finished").aggregate(v=Avg("score"))["v"] or 0
    active = Attempt.objects.filter(status="active").count()
    return render(request, "training/teacher_dashboard.html", {"assignments": assignments, "scenarios": scenarios, "attempts": attempts, "avg_score": round(avg_score), "active": active})


@login_required
@role_required("trainee")
def trainee_dashboard(request):
    assignments = Assignment.objects.filter(trainee=request.user).select_related("scenario")
    attempts = Attempt.objects.filter(trainee=request.user).select_related("assignment__scenario")
    return render(request, "training/trainee_dashboard.html", {"assignments": assignments, "attempts": attempts, "avg_score": round(attempts.filter(status="finished").aggregate(v=Avg("score"))["v"] or 0)})


@login_required
@role_required("teacher")
def scenario_list(request):
    scenarios = Scenario.objects.all()
    return render(request, "training/scenarios.html", {"scenarios": scenarios})


@login_required
@role_required("teacher")
def scenario_create(request):
    if request.method == "POST":
        form = ScenarioForm(request.POST)
        if form.is_valid():
            scenario = form.save(commit=False)
            scenario.created_by = request.user
            scenario.save()
            audit(request, "Создана учебная карточка", "Scenario", scenario.id)
            messages.success(request, "Учебная карточка сохранена.")
            return redirect("scenario_list")
    else:
        form = ScenarioForm()
    return render(request, "training/scenario_form.html", {"form": form, "title": "Новая учебная карточка"})


@login_required
@role_required("teacher")
def scenario_edit(request, pk):
    scenario = get_object_or_404(Scenario, pk=pk)
    if request.method == "POST":
        form = ScenarioForm(request.POST, instance=scenario)
        if form.is_valid():
            form.save()
            correction = request.POST.get("teacher_correction", "").strip()
            if correction:
                TeacherCorrection.objects.create(scenario=scenario, teacher=request.user, correction=correction)
            audit(request, "Изменена учебная карточка", "Scenario", scenario.id)
            messages.success(request, "Изменения сохранены.")
            return redirect("scenario_list")
    else:
        form = ScenarioForm(instance=scenario)
    return render(request, "training/scenario_form.html", {"form": form, "title": "Редактирование учебной карточки", "scenario": scenario})


@login_required
@role_required("teacher")
def assignment_create(request):
    if request.method == "POST":
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.teacher = request.user
            assignment.save()
            audit(request, "Назначено учебное занятие", "Assignment", assignment.id)
            messages.success(request, "Занятие назначено.")
            return redirect("teacher_dashboard")
    else:
        form = AssignmentForm()
    return render(request, "training/assignment_form.html", {"form": form})


@login_required
@role_required("teacher")
def report_list(request):
    attempts = Attempt.objects.select_related("assignment__scenario", "trainee").filter(status__in=["finished", "expired"])
    return render(request, "training/reports.html", {"attempts": attempts})


@login_required
@role_required("teacher")
def report_detail(request, pk):
    attempt = get_object_or_404(Attempt.objects.select_related("assignment__scenario", "trainee"), pk=pk)
    card = getattr(attempt, "card", None)
    statuses = attempt.status_records.select_related("author").all()
    events = attempt.events.all()
    return render(request, "training/report_detail.html", {"attempt": attempt, "card": card, "statuses": statuses, "events": events})


@login_required
@role_required("teacher")
def generate_scenario_view(request):
    if request.method != "POST":
        return redirect("scenario_list")
    category = request.POST.get("category", "Пожар и задымление")
    difficulty = request.POST.get("difficulty", "Средняя")
    corrections = list(TeacherCorrection.objects.filter(applied=True).values_list("correction", flat=True)[:20])
    try:
        data = generate_scenario(category, difficulty, corrections=corrections)
        scenario = Scenario.objects.create(
            title=data.get("title", f"{category} — учебная карточка"),
            category=category,
            difficulty={"Базовая": 1, "Средняя": 2, "Повышенная": 3}.get(difficulty, 2),
            initial_message=data.get("initial_message", ""),
            expected=data.get("expected", {}),
            services=data.get("services", []),
            fields=data.get("fields", []),
            response_algorithm=data.get("response_algorithm", []),
            service_contacts=data.get("service_contacts", []),
            ai_generated=True,
            approved=False,
            created_by=request.user,
        )
        audit(request, "Сформирована учебная карточка", "Scenario", scenario.id)
        messages.success(request, "Карточка сформирована и ожидает утверждения преподавателем.")
    except Exception as exc:
        messages.error(request, f"Не удалось сформировать карточку: {exc}")
    return redirect("scenario_list")


@login_required
@role_required("trainee")
def start_attempt(request, assignment_id):
    assignment = get_object_or_404(Assignment.objects.select_related("scenario"), pk=assignment_id, trainee=request.user)
    if assignment.status == "done":
        return redirect("trainee_dashboard")
    attempt = Attempt.objects.create(assignment=assignment, trainee=request.user)
    scenario = assignment.scenario
    expected = scenario.expected or {}
    card = IncidentCard.objects.create(
        attempt=attempt,
        incident_number=f"112-{attempt.id:06d}",
        event_type=str(expected.get("event_type", scenario.category)),
        address=str(expected.get("address", "")),
        details=str(expected.get("details", scenario.initial_message)),
        apartment=str(expected.get("apartment", "")),
        entrance=str(expected.get("entrance", "")),
        floor=str(expected.get("floor", "")),
        people_inside=str(expected.get("people_inside", "")),
        children=str(expected.get("children", "")),
        injured=str(expected.get("injured", "")),
        open_fire=str(expected.get("open_fire", "")),
        receiving_departments=scenario.services or [],
    )
    assignment.status = "active"
    assignment.save(update_fields=["status"])
    AttemptEvent.objects.create(attempt=attempt, event_type="start", payload={"incident_number": card.incident_number})
    audit(request, "Начато учебное занятие", "Attempt", attempt.id)
    return redirect("arm112", attempt_id=attempt.id)


@login_required
@role_required("trainee")
def arm112(request, attempt_id):
    attempt = get_object_or_404(Attempt.objects.select_related("assignment__scenario"), pk=attempt_id, trainee=request.user)
    if attempt.status != "active":
        return redirect("attempt_result", attempt_id=attempt.id)
    scenario = attempt.assignment.scenario
    card = get_object_or_404(IncidentCard, attempt=attempt)
    statuses = list(attempt.status_records.values("status", "comment", "created_at"))
    return render(request, "training/arm112.html", {
        "attempt": attempt,
        "scenario": scenario,
        "card": card,
        "statuses": statuses,
        "service_contacts": scenario.service_contacts or [],
        "queue_count": min(3, max(0, Scenario.objects.filter(approved=True).count() - 1)),
    })


@login_required
@role_required("trainee")
@require_POST
def attempt_open(request, attempt_id):
    attempt = get_object_or_404(Attempt, pk=attempt_id, trainee=request.user, status="active")
    if attempt.accepted_at:
        return JsonResponse({"ok": True, "reaction_time": round(attempt.reaction_time, 1)})
    now = timezone.now()
    attempt.accepted_at = now
    attempt.reaction_time = max(0, (now - attempt.started_at).total_seconds())
    attempt.save(update_fields=["accepted_at", "reaction_time"])
    AttemptEvent.objects.create(attempt=attempt, event_type="card_opened", payload={"reaction_time": attempt.reaction_time})
    return JsonResponse({"ok": True, "reaction_time": round(attempt.reaction_time, 1)})


@login_required
@role_required("trainee")
@require_POST
def save_dds_note(request, attempt_id):
    attempt = get_object_or_404(Attempt, pk=attempt_id, trainee=request.user, status="active")
    payload = json.loads(request.body.decode("utf-8"))
    card = get_object_or_404(IncidentCard, attempt=attempt)
    card.operator_note = str(payload.get("operator_note", ""))
    card.validation_note = str(payload.get("validation_note", ""))
    card.save(update_fields=["operator_note", "validation_note", "updated_at"])
    if not attempt.first_record_at and (card.operator_note.strip() or card.validation_note.strip()):
        attempt.first_record_at = timezone.now()
        attempt.fill_time = max(0, (attempt.first_record_at - (attempt.accepted_at or attempt.started_at)).total_seconds())
        attempt.save(update_fields=["first_record_at", "fill_time"])
    AttemptEvent.objects.create(attempt=attempt, event_type="comment_saved", payload=payload)
    return JsonResponse({"ok": True})


@login_required
@role_required("trainee")
@require_POST
def add_status(request, attempt_id):
    attempt = get_object_or_404(Attempt, pk=attempt_id, trainee=request.user, status="active")
    payload = json.loads(request.body.decode("utf-8"))
    status = str(payload.get("status", ""))
    allowed = {x[0]: x[1] for x in CardStatus.STATUS_CHOICES}
    if status not in allowed:
        return JsonResponse({"ok": False, "error": "Неизвестный статус"}, status=400)
    comment = str(payload.get("comment", "")).strip()
    if status == "refused" and not comment:
        return JsonResponse({"ok": False, "error": "Для отказа укажите мотивированную причину"}, status=400)
    if not attempt.accepted_at:
        now = timezone.now()
        attempt.accepted_at = now
        attempt.reaction_time = max(0, (now - attempt.started_at).total_seconds())
    if not attempt.first_record_at:
        attempt.first_record_at = timezone.now()
        attempt.fill_time = max(0, (attempt.first_record_at - (attempt.accepted_at or attempt.started_at)).total_seconds())
    attempt.save(update_fields=["accepted_at", "reaction_time", "first_record_at", "fill_time"])
    record = CardStatus.objects.create(attempt=attempt, status=status, comment=comment, author=request.user)
    AttemptEvent.objects.create(attempt=attempt, event_type="status", payload={"status": status, "comment": comment})
    return JsonResponse({"ok": True, "status": allowed[status], "created_at": timezone.localtime(record.created_at).strftime("%H:%M:%S")})


@login_required
@role_required("trainee")
@require_POST
def service_call(request, attempt_id):
    attempt = get_object_or_404(Attempt.objects.select_related("assignment__scenario"), pk=attempt_id, trainee=request.user, status="active")
    payload = json.loads(request.body.decode("utf-8"))
    service = str(payload.get("service", "")).strip()
    status = str(payload.get("status", "")).strip()
    comment = str(payload.get("comment", "")).strip()
    if not service:
        return JsonResponse({"ok": False, "error": "Выберите службу"}, status=400)
    reply = generate_service_reply(attempt.assignment.scenario, service, status, comment)
    transcript = attempt.transcript or []
    transcript.append({"direction": "out", "service": service, "text": comment, "at": timezone.localtime().strftime("%H:%M:%S")})
    transcript.append({"direction": "in", "service": service, "text": reply, "at": timezone.localtime().strftime("%H:%M:%S")})
    attempt.transcript = transcript
    attempt.save(update_fields=["transcript"])
    AttemptEvent.objects.create(attempt=attempt, event_type="service_call", payload={"service": service, "status": status, "reply": reply})
    return JsonResponse({"ok": True, "reply": reply})


@login_required
@role_required("trainee")
@require_POST
def finish_attempt(request, attempt_id):
    attempt = get_object_or_404(Attempt.objects.select_related("assignment__scenario"), pk=attempt_id, trainee=request.user, status="active")
    card = get_object_or_404(IncidentCard, attempt=attempt)
    scenario = attempt.assignment.scenario
    now = timezone.now()
    if not attempt.accepted_at:
        attempt.accepted_at = now
        attempt.reaction_time = max(0, (now - attempt.started_at).total_seconds())
    if not attempt.first_record_at:
        attempt.first_record_at = now
        attempt.fill_time = max(0, (now - attempt.accepted_at).total_seconds())
    statuses = list(attempt.status_records.values("status", "comment"))
    payload = {"event_type": card.event_type, "address": card.address, "details": card.details, "apartment": card.apartment, "entrance": card.entrance, "floor": card.floor, "people_inside": card.people_inside, "children": card.children, "injured": card.injured, "open_fire": card.open_fire}
    score, grammar_score, errors, feedback = evaluate_attempt(scenario, payload, statuses, attempt.reaction_time, attempt.fill_time)
    attempt.finished_at = now
    attempt.score = score
    attempt.grammar_score = grammar_score
    attempt.errors = errors
    attempt.ai_feedback = feedback
    attempt.status = "finished"
    attempt.save()
    attempt.assignment.status = "done"
    attempt.assignment.save(update_fields=["status"])
    AttemptEvent.objects.create(attempt=attempt, event_type="finish", payload={"score": score, "errors": errors})
    audit(request, "Завершено учебное занятие", "Attempt", attempt.id)
    return JsonResponse({"ok": True, "redirect": f"/attempts/{attempt.id}/result/"})


@login_required
def attempt_result(request, attempt_id):
    attempt = get_object_or_404(Attempt.objects.select_related("assignment__scenario", "trainee"), pk=attempt_id)
    if request.user != attempt.trainee and not request.user.is_superuser and (not hasattr(request.user, "profile") or request.user.profile.role != "teacher"):
        return HttpResponseForbidden("Доступ запрещён")
    return render(request, "training/result.html", {"attempt": attempt, "card": getattr(attempt, "card", None), "statuses": attempt.status_records.select_related("author")})


@login_required
@role_required("teacher")
def trainee_detail(request, user_id):
    trainee = get_object_or_404(User, pk=user_id)
    attempts = Attempt.objects.filter(trainee=trainee, status="finished").select_related("assignment__scenario")
    stats = attempts.aggregate(avg=Avg("score"), count=Count("id"))
    return render(request, "training/trainee_detail.html", {"trainee": trainee, "attempts": attempts, "stats": stats})


@login_required
def api_status(request):
    return JsonResponse({"status": "ok", "server_time": timezone.now().isoformat(), "user": request.user.username})
