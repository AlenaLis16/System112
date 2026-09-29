import os
import subprocess
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        out = Path(settings.BASE_DIR) / "backups"
        out.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db = settings.DATABASES["default"]
        if db["ENGINE"].endswith("postgresql"):
            file = out / f"simulator112_{stamp}.sql"
            env = os.environ.copy()
            env["PGPASSWORD"] = db["PASSWORD"]
            subprocess.run([
                "pg_dump", "-h", db["HOST"], "-p", str(db["PORT"]),
                "-U", db["USER"], "-d", db["NAME"], "-f", str(file)
            ], check=True, env=env)
            self.stdout.write(self.style.SUCCESS(str(file)))
        else:
            import shutil
            file = out / f"simulator112_{stamp}.sqlite3"
            shutil.copy2(db["NAME"], file)
            self.stdout.write(self.style.SUCCESS(str(file)))
