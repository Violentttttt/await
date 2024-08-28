# Generated by Django 5.0.6 on 2024-08-09 21:46

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('w84u', '0021_alter_marker_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='session_1',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='matches_as_session1', to='w84u.session'),
        ),
        migrations.AddField(
            model_name='match',
            name='session_2',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='matches_as_session2', to='w84u.session'),
        ),
        migrations.AlterField(
            model_name='match',
            name='user_1',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matches_as_user1', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='match',
            name='user_2',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matches_as_user2', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='MaybeMatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_confirmed_by_user1', models.BooleanField(default=False)),
                ('id_confirmed_by_user2', models.BooleanField(default=False)),
                ('session_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maybe_matches_as_session1', to='w84u.session')),
                ('session_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maybe_matches_as_session2', to='w84u.session')),
                ('user_1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maybe_mathes_as_user_1', to=settings.AUTH_USER_MODEL)),
                ('user_2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maybe_matches_as_user2', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
