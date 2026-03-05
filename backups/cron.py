from django_cron import CronJobBase, Schedule
from django.core.management import call_command

class MasterBackupCron(CronJobBase):
    RUN_AT_TIMES = ['03:00']  # Every day at 3 AM

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'backups.master_db_backup'

    def do(self):
        call_command("backup_master")