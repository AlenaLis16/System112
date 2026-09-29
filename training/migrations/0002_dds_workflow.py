from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("training", "0001_initial")]
    operations = [
        migrations.AddField(model_name="scenario", name="response_algorithm", field=models.JSONField(blank=True, default=list, verbose_name="Алгоритм реагирования")),
        migrations.AddField(model_name="scenario", name="service_contacts", field=models.JSONField(blank=True, default=list, verbose_name="Руководители реагирующих служб")),
        migrations.AddField(model_name="attempt", name="first_record_at", field=models.DateTimeField(blank=True, null=True, verbose_name="Первая запись")),
        migrations.AddField(model_name="incidentcard", name="incident_number", field=models.CharField(blank=True, max_length=30, verbose_name="Номер карточки")),
        migrations.AddField(model_name="incidentcard", name="receiving_departments", field=models.JSONField(blank=True, default=list, verbose_name="ДДС-получатели")),
        migrations.AddField(model_name="incidentcard", name="validation_note", field=models.TextField(blank=True, verbose_name="Замечание по карточке")),
        migrations.CreateModel(
            name="CardStatus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("accepted","Принято"),("not_accepted","Не принято"),("response_started","Начало реагирования"),("arrived","Прибытие"),("work","Проведение работ"),("completed","Завершение"),("refused","Отказ")], max_length=30, verbose_name="Статус карточки")),
                ("comment", models.TextField(blank=True, verbose_name="Комментарий")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Время")),
                ("attempt", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="status_records", to="training.attempt", verbose_name="Занятие")),
                ("author", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="auth.user", verbose_name="Автор")),
            ],
            options={"ordering":["created_at"],"verbose_name":"Статус карточки","verbose_name_plural":"Статусы карточек"},
        ),
        migrations.CreateModel(
            name="TeacherCorrection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("correction", models.TextField(verbose_name="Поправка преподавателя")),
                ("applied", models.BooleanField(default=True, verbose_name="Учитывать при генерации")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата")),
                ("scenario", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="corrections", to="training.scenario", verbose_name="Учебная карточка")),
                ("teacher", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="auth.user", verbose_name="Преподаватель")),
            ],
            options={"ordering":["-created_at"],"verbose_name":"Поправка преподавателя","verbose_name_plural":"Поправки преподавателей"},
        ),
        migrations.AlterField(model_name="profile", name="role", field=models.CharField(choices=[("teacher","Преподаватель"),("trainee","Диспетчер ДДС")], default="trainee", max_length=20, verbose_name="Роль")),
    ]
