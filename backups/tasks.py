from celery import shared_task
from customers.models import Client
from backups.services import generate_backup_for_tenant


@shared_task
def run_daily_backups():
    for client in Client.objects.all():
        generate_backup_for_tenant(client, "daily")


@shared_task
def run_weekly_backups():
    for client in Client.objects.all():
        generate_backup_for_tenant(client, "weekly")


@shared_task
def run_master_backups():
    for client in Client.objects.all():
        generate_backup_for_tenant(client, "master")