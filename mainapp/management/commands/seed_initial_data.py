# mainapp/management/commands/seed_initial_data.py
from django.core.management.base import BaseCommand
from mainapp.models import SiteInformation, FAQ


class Command(BaseCommand):
    help = 'Seed initial data (idempotent).'

    def handle(self, *args, **options):
        created_count = 1

        SiteInformation.objects.get_or_create(
            field='about_us',
            defaults={'text': 'This is the default placeholder for about us page'},
        )
        SiteInformation.objects.get_or_create(
            field='terms_of_service',
            defaults={'text': 'This is the default placeholder for terms of service page'},
        )

        FAQ.objects.get_or_create(
            priority=1,
            defaults={'title': 'Question one:', 'text': 'This is the default placeholder for first faq'},
        )


        if created_count:
            self.stdout.write(self.style.SUCCESS(f"\nSeeded initial rows."))
        else:
            self.stdout.write(self.style.WARNING("All rows already exist."))