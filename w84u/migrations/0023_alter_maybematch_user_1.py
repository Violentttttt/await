# Generated by Django 5.0.6 on 2024-08-11 19:32

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('w84u', '0022_match_session_1_match_session_2_alter_match_user_1_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='maybematch',
            name='user_1',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maybe_matсhes_as_user_1', to=settings.AUTH_USER_MODEL),
        ),
    ]
