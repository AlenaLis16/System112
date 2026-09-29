import json
import requests
from django.conf import settings

def ask_ollama(prompt, timeout=60):
    response = requests.post(
        f"{settings.OLLAMA_URL.rstrip('/')}/api/generate",
        json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json().get("response", "")

def parse_json(raw):
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Модель вернула данные в неверном формате")
    return json.loads(raw[start:end + 1])

def generate_scenario(category, difficulty, location="Москва", corrections=None):
    corrections_text = "\n".join(corrections or [])
    prompt = f'''Сформируй учебную карточку для тренажёра диспетчера ДДС системы 112 города Москвы.
Тип происшествия: {category}
Сложность: {difficulty}
Локация: {location}
Диспетчер ДДС НЕ принимает звонок заявителя. Карточка уже сформирована системой 112 и поступает в конкретную ДДС.
Нужны правдоподобные учебные данные без реальных персональных данных.
Укажи ДДС-получателей, руководителей реагирующих служб и ожидаемый цикл статусов: Принято, Не принято, Начало реагирования, Прибытие, Проведение работ, Завершение, Отказ.
Верни только JSON:
{{
"title":"",
"initial_message":"",
"expected":{{"event_type":"","address":"","details":"","apartment":"","entrance":"","floor":"","people_inside":"","children":"","injured":"","open_fire":""}},
"services":[],
"fields":[],
"response_algorithm":["Принято","Начало реагирования","Прибытие","Проведение работ","Завершение"],
"service_contacts":[{{"service":"","role":"Руководитель бригады","phone":""}}]
}}
Поправки преподавателей, которые необходимо учитывать:
{corrections_text}
'''
    return parse_json(ask_ollama(prompt))

def generate_service_reply(scenario, service, status, comment):
    prompt = f'''Сымитируй короткий служебный ответ руководителя реагирующей службы диспетчеру ДДС.
Происшествие: {scenario.title}
Адрес: {(scenario.expected or {}).get("address", "")}
Служба: {service}
Текущий статус: {status}
Комментарий диспетчера: {comment}
Ответ должен быть кратким, деловым, без выдуманных опасных инструкций и без персональных данных.
Верни только текст ответа на русском языке.'''
    try:
        return ask_ollama(prompt, timeout=30).strip()
    except Exception:
        return f"Служба «{service}»: информация принята. Работа по карточке продолжается."

def evaluate_attempt(scenario, card, statuses, reaction_time, first_record_time):
    expected = scenario.expected or {}
    errors = []
    score = 100
    required_fields = ["event_type", "address", "details"]
    for field in required_fields:
        target = str(expected.get(field, "")).strip().lower()
        actual = str(card.get(field, "")).strip().lower()
        if target and actual and target not in actual and actual not in target:
            errors.append({"field": field, "type": "mismatch", "message": "Данные карточки отличаются от учебной вводной"})
            score -= 8
    status_names = [s.get("status") for s in statuses]
    if not any(s in status_names for s in ["accepted", "not_accepted"]):
        errors.append({"field": "status", "type": "missing", "message": "Не установлен исходный статус карточки"})
        score -= 20
    if "not_accepted" in status_names:
        if not any(s.get("status") == "refused" and str(s.get("comment", "")).strip() for s in statuses):
            errors.append({"field": "refused", "type": "missing", "message": "Для отказа не указана мотивированная причина"})
            score -= 20
    else:
        for required in ["accepted", "response_started", "arrived", "work", "completed"]:
            if required not in status_names:
                errors.append({"field": required, "type": "missing", "message": "Не установлен обязательный статус"})
                score -= 10
    if reaction_time > scenario.reaction_limit:
        errors.append({"field": "reaction_time", "type": "timing", "message": "Карточка открыта позже норматива"})
        score -= 10
    if first_record_time > scenario.time_limit:
        errors.append({"field": "first_record_time", "type": "timing", "message": "Первая запись сделана позже норматива"})
        score -= 10
    comments = " ".join(str(s.get("comment", "")) for s in statuses)
    grammar_score = 100
    if len(comments.strip()) < 10:
        grammar_score = 85
    if "  " in comments:
        grammar_score -= 5
    score = max(0, min(100, score))
    feedback = "Обработка карточки завершена в соответствии с заданным алгоритмом." if not errors else "Выявлены отклонения по статусам, срокам или служебным комментариям."
    return score, grammar_score, errors, feedback
