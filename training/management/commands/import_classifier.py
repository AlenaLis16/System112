from pathlib import Path
from django.core.management.base import BaseCommand
from openpyxl import load_workbook
from training.models import Scenario

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--file", default="data/classifier.xlsx")

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.is_absolute():
            path = Path.cwd() / path
        wb = load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        imported = 0
        for row in ws.iter_rows(min_row=4, values_only=True):
            if len(row) < 15:
                continue
            number = row[4]
            category = row[5]
            sign1 = row[6]
            sign2 = row[7]
            sign3 = row[8]
            result = row[10]
            if not number and not result:
                continue
            title = result or category or sign1 or "Учебное происшествие"
            description = " / ".join(str(x) for x in [sign1, sign2, sign3] if x)
            Scenario.objects.get_or_create(
                title=str(title)[:200],
                classifier_code=str(number or ""),
                defaults={
                    "category": str(category or sign1 or "Происшествие"),
                    "description": description[:1000],
                    "difficulty": 1,
                    "time_limit": 180,
                    "reaction_limit": 30,
                    "approved": True,
                    "source_code": "classifier-2024",
                },
            )
            imported += 1
        self.stdout.write(self.style.SUCCESS(f"Импортировано: {imported}"))
