from django.core.management.base import BaseCommand
from mainapp.models import SiteInformation, FAQ
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def seed_site_data(self):
    SiteInformation.objects.get_or_create(
        field='about_us',
        defaults={'text': 'This is the default placeholder for about us page'},
    )
    SiteInformation.objects.get_or_create(
        field='terms_of_service',
        defaults={'text': 'This is the default placeholder for terms of service page'},
    )
    SiteInformation.objects.get_or_create(
        field='phone_number',
        defaults={'text': '+989150001516'},
    )
    SiteInformation.objects.get_or_create(
        field='footer_text',
        defaults={'text': 'thi is the placeholder text for the footer text area of the page'},
    )
    SiteInformation.objects.get_or_create(
        field='email',
        defaults={
            'text': 'example@site.com'},
    )
    SiteInformation.objects.get_or_create(
        field='address',
        defaults={
            'text': 'Brooklyn, New York'},
    )
    SiteInformation.objects.get_or_create(
        field='opening_hours',
        defaults={
            'text': 'Fri to Wed: 6:00 Am to 8:00 Pm'},
    )

    FAQ.objects.get_or_create(
        priority=1,
        defaults={'title': 'Question one:', 'text': 'This is the default placeholder for first faq'},
    )


def seed_groups(self):
    GROUPS = {
        'administrator': [
            ('account', 'emailaddress', ['add', 'view', 'change', 'delete']),
            ('mainapp', 'siteinformation', ['view', 'change']),
            ('mainapp', 'faq', ['add', 'view', 'change', 'delete']),
            ('mainapp', 'item', ['add', 'view', 'change', 'delete']),
            ('mainapp', 'order', ['add', 'view', 'change', 'delete']),
            ('mainapp', 'profile', ['add', 'view', 'change', 'delete']),
            ('mainapp', 'review', ['add', 'view', 'change', 'delete']),
            ('mainapp', 'category', ['add', 'view', 'change', 'delete']),
            ('admin', 'logentry', ['view']),
            ('auth', 'user', ['add', 'view', 'change', 'delete']),
        ],
        'staff_1': [
            ('account', 'emailaddress', ['view', 'change']),
            ('mainapp', 'siteinformation', ['view', 'change']),
            ('mainapp', 'faq', ['add', 'view', 'change', 'delete']),
            ('mainapp', 'item', ['add', 'view', 'change', 'delete']),
            ('mainapp', 'order', ['view', 'change']),
            ('mainapp', 'profile', ['add', 'view', 'change', 'delete']),
            ('mainapp', 'review', ['view', 'change', 'delete']),
            ('mainapp', 'category', ['add', 'view', 'change', 'delete']),
        ],
    }

    for group_name, perm in GROUPS.items():
        group, created = Group.objects.get_or_create(name=group_name)

        for app_label, model_name, actions in perm:
            try:
                ct = ContentType.objects.get(app_label=app_label, model=model_name)
            except ContentType.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"! Content type not found: {app_label}.{model_name}"
                ))
                continue

            for action in actions:
                codename = f"{action}_{model_name}"
                try:
                    perm = Permission.objects.get(content_type=ct, codename=codename)
                    group.permissions.add(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"! Permission not found: {codename}"
                    ))

class Command(BaseCommand):
    help = 'Seed initial data (idempotent).'

    def handle(self, *args, **options):
        created_count = 1

        seed_site_data(self)
        seed_groups(self)

        self.stdout.write(self.style.SUCCESS(f"\nSeeded initial rows."))


