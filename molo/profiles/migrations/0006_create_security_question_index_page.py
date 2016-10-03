from __future__ import unicode_literals

from django.db import migrations, models


def create_section_index(apps, schema_editor):
    from molo.core.models import Main
    from molo.profiles.models import SecurityQuestionIndexPage
    main = Main.objects.all().first()

    if main:
        section_index = SecurityQuestionIndexPage(title='Security Questions', slug='security-questions')
        main.add_child(instance=section_index)
        section_index.save_revision().publish()


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0005_add_security_question_models'),
    ]

    operations = [
        migrations.RunPython(create_section_index),
    ]
