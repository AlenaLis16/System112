from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("teacher/", views.teacher_dashboard, name="teacher_dashboard"),
    path("teacher/scenarios/", views.scenario_list, name="scenario_list"),
    path("teacher/scenarios/new/", views.scenario_create, name="scenario_create"),
    path("teacher/scenarios/<int:pk>/edit/", views.scenario_edit, name="scenario_edit"),
    path("teacher/scenarios/generate/", views.generate_scenario_view, name="generate_scenario"),
    path("teacher/assignments/new/", views.assignment_create, name="assignment_create"),
    path("teacher/reports/", views.report_list, name="report_list"),
    path("teacher/reports/<int:pk>/", views.report_detail, name="report_detail"),
    path("teacher/trainees/<int:user_id>/", views.trainee_detail, name="trainee_detail"),
    path("trainee/", views.trainee_dashboard, name="trainee_dashboard"),
    path("attempt/<int:assignment_id>/start/", views.start_attempt, name="start_attempt"),
    path("arm112/<int:attempt_id>/", views.arm112, name="arm112"),
    path("api/attempt/<int:attempt_id>/open/", views.attempt_open, name="attempt_open"),
    path("api/attempt/<int:attempt_id>/note/", views.save_dds_note, name="save_dds_note"),
    path("api/attempt/<int:attempt_id>/status/", views.add_status, name="add_status"),
    path("api/attempt/<int:attempt_id>/service-call/", views.service_call, name="service_call"),
    path("api/attempt/<int:attempt_id>/finish/", views.finish_attempt, name="finish_attempt"),
    path("attempts/<int:attempt_id>/result/", views.attempt_result, name="attempt_result"),
    path("api/status/", views.api_status, name="api_status"),
]
