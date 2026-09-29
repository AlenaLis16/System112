from django.contrib import admin
from .models import Assignment, Attempt, AttemptEvent, AuditLog, CardStatus, IncidentCard, Profile, Scenario, TeacherCorrection

admin.site.site_header = "ГБУ Система 112 — администрирование"
admin.site.site_title = "ГБУ Система 112"
admin.site.index_title = "Управление учебным комплексом"

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "group_name", "position")
    list_filter = ("role",)
    search_fields = ("user__username", "user__first_name", "user__last_name")

@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "difficulty", "reaction_limit", "time_limit", "approved", "ai_generated")
    list_filter = ("difficulty", "approved", "ai_generated", "category")
    search_fields = ("title", "category", "classifier_code")

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("scenario", "trainee", "teacher", "status", "created_at")
    list_filter = ("status",)

@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "trainee", "assignment", "score", "grammar_score", "status", "started_at")
    list_filter = ("status",)
    readonly_fields = ("started_at", "accepted_at", "finished_at", "first_record_at")

@admin.register(IncidentCard)
class IncidentCardAdmin(admin.ModelAdmin):
    list_display = ("incident_number", "attempt", "event_type", "address", "updated_at")
    search_fields = ("incident_number", "address", "event_type")

@admin.register(CardStatus)
class CardStatusAdmin(admin.ModelAdmin):
    list_display = ("attempt", "status", "author", "created_at")
    list_filter = ("status",)

@admin.register(AttemptEvent)
class AttemptEventAdmin(admin.ModelAdmin):
    list_display = ("attempt", "event_type", "created_at")
    list_filter = ("event_type",)

@admin.register(TeacherCorrection)
class TeacherCorrectionAdmin(admin.ModelAdmin):
    list_display = ("scenario", "teacher", "applied", "created_at")
    list_filter = ("applied",)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action", "object_type", "object_id", "ip_address")
    list_filter = ("action", "object_type")
    search_fields = ("action", "user__username")
