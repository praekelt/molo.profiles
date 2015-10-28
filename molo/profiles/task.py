from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.conf import settings
from celery.task import periodic_task
from celery.schedules import crontab
import requests


def get_count_of_new_users():
    now = datetime.now()
    qs = User.objects.filter(date_joined__gte=now - timedelta(hours=24))
    return qs.count()


def get_count_of_returning_users():
    now = datetime.now()
    qs = User.objects.filter(last_login__gte=now - timedelta(hours=24)).filter(
        date_joined__lt=now - timedelta(hours=24))
    return qs.count()


def get_count_of_all_users():
    qs = User.objects.all()
    return qs.count()


def get_message_text():
    return ("DAILY UPDATE ON USER DATA\n"
            "New User - joined in the last 24 hours\n"
            "Returning User - joined longer than 24 hours ago"
            "and visited the site in the last 24 hours\n"
            "```"
            "Total Users: {0}\n"
            "New Users: {1}\n"
            "Returning Users: {2}"
            "```"
            .format(get_count_of_all_users(),
                    get_count_of_new_users(),
                    get_count_of_returning_users()))


@periodic_task(run_every=crontab(hour='8'))
def send_announcement():
    try:
        url = settings.SLACK_INCOMING_WEBHOOK_URL
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        data = {
            "text": get_message_text()
        }
        print"HELLO!"
        requests.post(url, data=data, headers=headers)
        print"GOODBYE!"
    except AttributeError:
        pass
