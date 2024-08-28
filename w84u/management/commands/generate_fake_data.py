import pytz
from django.core.management.base import BaseCommand
from faker import Faker
from w84u.models import CustomUser, Marker, Session, OptionalInfo
from django.utils import timezone
from django.db.utils import IntegrityError
from django.contrib.gis.geos import Point
from psycopg2.extras import DateTimeTZRange

fake = Faker()

class Command(BaseCommand):
    help = 'Generate fake data for CustomUser, Marker, and Session'

    def handle(self, *args, **kwargs):
        # Очистка таблиц перед созданием новых данных
        # CustomUser.objects.all().delete()
        # Marker.objects.all().delete()
        # Session.objects.all().delete()
        # OptionalInfo.objects.all().delete()

        usernames = set()
        emails = set()
        for _ in range(100):
            username = fake.user_name()
            while username in usernames:
                username = fake.user_name()
            usernames.add(username)

            email = fake.email()
            while email in emails:
                email = fake.email()
            emails.add(email)

            try:
                user = CustomUser.objects.create(
                    email=email,
                    username=username,
                    real_name=fake.name(),
                    age=fake.random_int(min=18, max=80),
                    gender=fake.random_element(elements=('men', 'women')),
                    created_at=fake.date_time_this_decade(tzinfo=pytz.UTC),
                    is_active=True,
                    is_staff=fake.boolean(),
                    is_superuser=fake.boolean(),
                    more_info=None
                )

                OptionalInfo.objects.create(
                    user=user,
                    image=None,
                    surname=fake.last_name(),
                    about=fake.text(max_nb_chars=500),
                    country=fake.country(),
                    town=fake.city(),
                    study=fake.word(),
                    work=fake.job()
                )

                red_marker_location = Point(float(fake.longitude()), float(fake.latitude()))
                blue_marker_location = Point(float(fake.longitude()), float(fake.latitude()))

                red_marker = Marker.objects.create(
                    user=user,
                    location=red_marker_location,
                    type='red',
                    created_at=timezone.now()
                )

                blue_marker = Marker.objects.create(
                    user=user,
                    location=blue_marker_location,
                    type='blue',
                    created_at=timezone.now()
                )

                for _ in range(3):
                    use_datetime_range = fake.boolean()

                    if use_datetime_range:
                        start_datetime = fake.date_time_this_decade(tzinfo=pytz.UTC)
                        end_datetime = fake.date_time_between(start_date=start_datetime, tzinfo=pytz.UTC)

                        Session.objects.create(
                            user=user,
                            red_marker=red_marker,
                            blue_marker=blue_marker,
                            name=fake.word(),
                            gender=user.gender,
                            datetime_range=DateTimeTZRange(start_datetime, end_datetime),
                            surname=fake.last_name(),
                            image=None,
                            more_info=fake.text(max_nb_chars=500),
                            is_active=fake.boolean(),
                            created_at=timezone.now()
                        )
                    else:
                        date = fake.date_time_this_decade(tzinfo=pytz.UTC)

                        Session.objects.create(
                            user=user,
                            red_marker=red_marker,
                            blue_marker=blue_marker,
                            name=fake.word(),
                            gender=user.gender,
                            date=date,
                            datetime_range=None,
                            surname=fake.last_name(),
                            image=None,
                            more_info=fake.text(max_nb_chars=500),
                            is_active=fake.boolean(),
                            created_at=timezone.now()
                        )

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f'Error creating user or related data: {e}'))

        self.stdout.write(self.style.SUCCESS('Successfully generated fake data'))
