# Generated by Django 5.0.6 on 2024-08-12 13:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('w84u', '0023_alter_maybematch_user_1'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='match',
            unique_together={('user_1', 'session_1', 'user_2', 'session_2')},
        ),
    ]
