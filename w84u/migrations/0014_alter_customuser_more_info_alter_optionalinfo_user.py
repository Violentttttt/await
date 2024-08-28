# Generated by Django 5.0.6 on 2024-08-03 00:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('w84u', '0013_optionalinfo_customuser_more_info'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='more_info',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='w84u.optionalinfo'),
        ),
        migrations.AlterField(
            model_name='optionalinfo',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
