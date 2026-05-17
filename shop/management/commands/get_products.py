from django.core.management.base import BaseCommand, CommandError

from shop.services.crawler import ProductCrawler


class Command(BaseCommand):
    help = "Collect products from source"

    def handle(self, *args, **options):
        try:
            print("COMMAND STARTED")
            summary = ProductCrawler().execute()
        except Exception as error:
            raise CommandError(f"Error {error}") from error

        self.stdout.write(self.style.SUCCESS(f"Successfully executed: {summary}"))
