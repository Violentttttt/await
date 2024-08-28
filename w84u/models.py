# models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import DateTimeRangeField
from django.contrib.gis.db import models as gis_models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        OptionalInfo.objects.create(user=user)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)
    real_name = models.CharField(max_length=100)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=(('men', 'Men'), ('women', 'Women')))
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    more_info = models.OneToOneField('OptionalInfo', on_delete=models.CASCADE, null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


class OptionalInfo(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='OptionalInfo_images/', null=True, blank=True)
    surname = models.CharField(max_length=100, null=True, blank=True)
    about = models.CharField(max_length=500, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    town = models.CharField(max_length=100, null=True, blank=True)
    study = models.CharField(max_length=100, null=True, blank=True)
    work = models.CharField(max_length=100, null=True, blank=True)


class Marker(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    location = gis_models.PointField()
    type = models.CharField(max_length=10, choices=(('red', 'Red'), ('blue', 'Blue')))
    created_at = models.DateTimeField(default=timezone.now)

    # class Meta:
    #     unique_together = ('user', 'type')


class MarkerHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    marker = models.ForeignKey(Marker, on_delete=models.CASCADE)
    match = models.ForeignKey('Match', on_delete=models.CASCADE, default=1)
    latitude = models.FloatField()
    longitude = models.FloatField()
    requested_at = models.DateTimeField(default=timezone.now)


class Match(models.Model):
    user_1 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='matches_as_user1')
    session_1 = models.ForeignKey('Session', on_delete=models.CASCADE, related_name='matches_as_session1', null=True)
    user_2 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='matches_as_user2')
    session_2 = models.ForeignKey('Session', on_delete=models.CASCADE, related_name='matches_as_session2', null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user_1', 'session_1', 'user_2', 'session_2')


class Message(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)


class MaybeMatch(models.Model):
    user_1 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='maybe_matсhes_as_user_1')#тот , кого ищет пользователь
    session_1 = models.ForeignKey('Session', on_delete=models.CASCADE, related_name='maybe_matches_as_session1')#сессия пользователя , в которой ищут первого юзера
    id_confirmed_by_user1 = models.BooleanField(default=False)
    user_2 = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='maybe_matches_as_user2')#пользователь
    session_2 = models.ForeignKey('Session', on_delete=models.CASCADE, related_name='maybe_matches_as_session2')
    id_confirmed_by_user2 = models.BooleanField(default=False)

    def is_fully_confirmed(self):
        return self.is_confirmed_by_user1 and self.is_confirmed_by_user2


class Session(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    red_marker = models.OneToOneField(Marker, related_name='red_marker_session', on_delete=models.CASCADE, null=True,
                                      blank=True)
    blue_marker = models.OneToOneField(Marker, related_name='blue_marker_session', on_delete=models.CASCADE, null=True,
                                       blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=(('men', 'Men'), ('women', 'Women')))
    date = models.DateTimeField(null=True, blank=True)
    datetime_range = DateTimeRangeField(null=True, blank=True)
    surname = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to='session_images/', null=True, blank=True)
    more_info = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.id},{self.name} ({self.date}),{self.datetime_range},{self.red_marker},{self.blue_marker}, {self.surname}'
