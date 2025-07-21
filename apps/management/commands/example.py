from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Tu lógica aquí
        print("Ejecutando tarea programada...")

        return "Completado"