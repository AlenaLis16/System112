from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from training.models import Assignment, Profile, Scenario

class Command(BaseCommand):
    help = "Создаёт демонстрационные учетные записи и учебные карточки"

    def handle(self, *args, **options):
        teacher, _ = User.objects.get_or_create(username="teacher")
        teacher.first_name = "Анна"
        teacher.last_name = "Соколова"
        teacher.set_password("Teacher112!")
        teacher.save()
        Profile.objects.update_or_create(user=teacher, defaults={"role": "teacher", "position": "Преподаватель"})

        trainee, _ = User.objects.get_or_create(username="trainee")
        trainee.first_name = "Иван"
        trainee.last_name = "Петров"
        trainee.set_password("Trainee112!")
        trainee.save()
        Profile.objects.update_or_create(user=trainee, defaults={"role": "trainee", "group_name": "ДДС-01", "position": "Диспетчер ДДС"})

        scenarios = [
            {
                "title": "Пожар в школе",
                "category": "Пожар и задымление",
                "classifier_code": "1010101",
                "difficulty": 2,
                "time_limit": 180,
                "reaction_limit": 30,
                "description": "Карточка поступила в ДДС по сообщению системы 112 о пожаре в образовательном учреждении.",
                "initial_message": "Поступила карточка: пожар в школе, есть пострадавшие. Карточка направлена в ДДС, участвующие в реагировании.",
                "expected": {"event_type": "пожар в школе", "address": "Москва, улица Новая, дом 18", "details": "открытое пламя и задымление в здании школы", "apartment": "", "entrance": "1", "floor": "2", "people_inside": "есть", "children": "есть", "injured": "2", "open_fire": "да"},
                "services": ["ДДС образования", "ДДС управы района", "ДДС Сев-Западного административного округа"],
                "fields": ["Адрес", "Этаж", "Пострадавшие", "Состояние объекта", "Взаимодействие со службами"],
                "response_algorithm": ["Принято", "Начало реагирования", "Прибытие", "Проведение работ", "Завершение"],
                "service_contacts": [{"service": "Пожарно-спасательная служба", "role": "Руководитель бригады", "phone": "Внутренний номер"}, {"service": "Мосэнерго", "role": "Дежурный", "phone": "Внутренний номер"}],
            },
            {
                "title": "ДТП с пострадавшим",
                "category": "Дорожно-транспортное происшествие",
                "classifier_code": "2020101",
                "difficulty": 2,
                "time_limit": 180,
                "reaction_limit": 30,
                "description": "Карточка поступила в ДДС по сообщению системы 112 о столкновении автомобилей.",
                "initial_message": "Поступила карточка: ДТП с пострадавшим, движение затруднено.",
                "expected": {"event_type": "ДТП", "address": "Москва, Ленинградский проспект, дом 36", "details": "столкновение двух легковых автомобилей, один человек пострадал", "apartment": "", "entrance": "", "floor": "", "people_inside": "2", "children": "", "injured": "1", "open_fire": "нет"},
                "services": ["ДДС скорой медицинской помощи", "ДДС полиции", "Автомобильные дороги"],
                "fields": ["Адрес", "Пострадавшие", "Количество автомобилей", "Состояние движения"],
                "response_algorithm": ["Принято", "Начало реагирования", "Прибытие", "Проведение работ", "Завершение"],
                "service_contacts": [{"service": "Скорая медицинская помощь", "role": "Старший бригады", "phone": "Внутренний номер"}, {"service": "Полиция", "role": "Старший группы", "phone": "Внутренний номер"}],
            },
            {
                "title": "Запах газа в подъезде",
                "category": "Газ",
                "classifier_code": "3030101",
                "difficulty": 3,
                "time_limit": 180,
                "reaction_limit": 30,
                "description": "Карточка поступила в ДДС по сообщению системы 112 о запахе газа в жилом доме.",
                "initial_message": "Поступила карточка: сильный запах газа в подъезде. Люди выведены.",
                "expected": {"event_type": "запах газа", "address": "Москва, улица Садовая, дом 7", "details": "сильный запах газа в подъезде", "apartment": "", "entrance": "1", "floor": "1-2", "people_inside": "0", "children": "", "injured": "нет", "open_fire": "нет"},
                "services": ["ДДС газовой службы", "ДДС управы района"],
                "fields": ["Адрес", "Подъезд", "Этаж", "Люди на месте", "Состояние объекта"],
                "response_algorithm": ["Принято", "Начало реагирования", "Прибытие", "Проведение работ", "Завершение"],
                "service_contacts": [{"service": "Газовая служба", "role": "Руководитель бригады", "phone": "Внутренний номер"}],
            },
        ]
        for item in scenarios:
            scenario, _ = Scenario.objects.update_or_create(title=item["title"], defaults={**item, "created_by": teacher, "approved": True, "ai_generated": False})
            Assignment.objects.get_or_create(scenario=scenario, trainee=trainee, defaults={"teacher": teacher})
        self.stdout.write(self.style.SUCCESS("Демонстрационная среда готова."))
        self.stdout.write("teacher / Teacher112!")
        self.stdout.write("trainee / Trainee112!")
