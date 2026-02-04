import datetime
import hashlib
import os
import uuid

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.db.models import ForeignKey
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.user.managers import CustomerManager


# Create your models here.


class CustomUser(AbstractUser):
    last_name = None
    first_name = None
    username = models.CharField(verbose_name='Phone Number', max_length=100, unique=True)
    name = models.CharField(verbose_name='Full Name', max_length=100)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    f_name = models.CharField(verbose_name='Fathers Name', max_length=100, null=True, blank=True)
    m_name = models.CharField(verbose_name='Mothers Name', max_length=100, null=True, blank=True)
    occupation = models.CharField(verbose_name='Occupation', max_length=100, null=True, blank=True)
    email = models.EmailField(verbose_name='Email Address', unique=True, null=True, blank=True)
    photo = models.ImageField(upload_to='user_photo', null=True, blank=True)
    cover_photo = models.ImageField(upload_to='user_photo', null=True, blank=True)
    signature = models.ImageField(upload_to='signature', null=True, blank=True)
    nid = models.CharField(max_length=30, null=True, blank=True)
    dob = models.DateField(verbose_name='Date of Birth', null=True, blank=True)
    address = models.TextField(verbose_name='Address', null=True, blank=True)
    bio = models.TextField(blank=True)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    updated_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = self.name.replace(' ', '-').lower()
            slug = base_slug
            if CustomUser.objects.filter(slug=slug).exists():
                import random
                random_number = str(random.randint(100000, 999999))
                slug = f"{base_slug}-{random_number}"
            self.slug = slug
        super(CustomUser, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.username)

    def get_display_name(self):
        """
        Helper to return preferred display name: name > email > username.
        """
        if getattr(self, 'name', None):
            return self.name
        if getattr(self, 'email', None):
            return self.email
        return self.username


class Staff(CustomUser):
    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        self.is_staff = True
        super(Staff, self).save(*args, **kwargs)
        group, created = Group.objects.get_or_create(name='staff')
        self.groups.set([group])


class Customer(CustomUser):
    class Meta:
        proxy = True

    objects = CustomerManager()

    def save(self, *args, **kwargs):
        self.is_staff = False
        super(Customer, self).save(*args, **kwargs)
        group, created = Group.objects.get_or_create(name='customer')
        self.groups.set([group])


class OtpToken(models.Model):
    user = models.CharField(max_length=255, editable=False)
    otp = models.CharField(max_length=40, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    attempts = models.IntegerField(default=0)
    used = models.BooleanField(default=False)
    is_password_reset = models.BooleanField(default=False)
    reset_key = models.CharField(max_length=255, unique=True, null=True, blank=True)
    reset_link = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "OTP Token"
        verbose_name_plural = "OTP Tokens"

    def __str__(self):
        return "{} - {}".format(self.user, self.otp)

    @classmethod
    def create_otp_for_user(cls, email, is_password_reset=None):
        today_min = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        today_max = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
        otps = cls.objects.filter(user=email, timestamp__range=(today_min, today_max))

        if otps.count() <= getattr(settings, 'PHONE_LOGIN_ATTEMPTS', 100000):
            otp = cls.generate_otp(length=getattr(settings, 'PHONE_LOGIN_OTP_LENGTH', 4))
            if is_password_reset:
                user = CustomUser.objects.get(email=email)
                url = f'https://housing.ac/password_reset_confirm/?otp={otp}&key={user.uuid}'
                otp_token = OtpToken(user=email, otp=otp, is_password_reset=is_password_reset, reset_link=url)
            else:
                otp_token = OtpToken(user=email, otp=otp)
            otp_token.save()
            print(f'Your otp is {otp}')
            # if otp_token.is_password_reset:
            #     user = CustomUser.objects.get(email=email)
            #     context = {
            #         'otp': otp,
            #         'email': email,
            #         'key': user.uuid,
            #     }
            #     print(user.uuid)
            #     html_content = render_to_string('password_reset.html', context)
            # else:
            #     context = {
            #         'otp': otp,
            #         'email': email
            #     }
            #     html_content = render_to_string('otp.html', context)

            # html_content = render_to_string('email_template.html', context)

            # message = Mail(
            #     from_email='noreply@iou.ac',
            #     to_emails=email,
            #     subject='OTP for IOU',
            #     html_content=html_content
            # )
            # try:
            #     sg = SendGridAPIClient('SG.dsffsdfs.gFMCBXtxrPCj7C9jaD3Ya7MU_5jzWy9IzKN4erF-wGQ')
            #     response = sg.send(message)
            #     print(response.status_code)
            #     print(response.body)
            #     print(response.headers)
            # except Exception as e:
            #     print(str(e))

            return otp_token
        else:
            return False

    @classmethod
    def generate_otp(cls, length=4):
        hash_algorithm = getattr(settings, 'PHONE_LOGIN_OTP_HASH_ALGORITHM', 'sha256')
        m = getattr(hashlib, hash_algorithm)()
        m.update(getattr(settings, 'SECRET_KEY', None).encode('utf-8'))
        m.update(os.urandom(16))
        # otp = str(int(m.hexdigest(), 16))[-length:]
        otp = 1234
        return otp
