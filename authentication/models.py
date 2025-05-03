from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.conf import settings
import re

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of username.
    """
    def create_user(self, username, university_email, password=None, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not university_email:
            raise ValueError(_('The University Email must be set'))
        if not username:
            raise ValueError(_('Username must be set'))
        
        email = self.normalize_email(university_email)
        user = self.model(
            username=username,
            university_email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, university_email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(
            username=username,
            university_email=university_email,
            password=password,
            **extra_fields
        )

    def get_by_natural_key(self, username):
        return self.get(
            models.Q(username__iexact=username) | 
            models.Q(university_email__iexact=username)
        )

class CustomUser(AbstractUser):
    """
    Custom user model that uses university email as primary identifier.
    """
    pass
    university_email = models.EmailField(
        _('university email'),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        },
        help_text=_('Required. Must be a valid ASTU email address ending with @astu.edu.et')
    )
    is_student = models.BooleanField(
        _('student status'),
        default=True,
        help_text=_('Designates whether the user is a student.')
    )
    is_admin = models.BooleanField(
        _('admin status'),
        default=False,
        help_text=_('Designates whether the user has admin privileges.')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        )
    )
    
    objects = CustomUserManager()
    
    # Make email field point to university_email for compatibility
    EMAIL_FIELD = 'university_email'
    USERNAME_FIELD = 'university_email'
    REQUIRED_FIELDS = ['username']
    
    def clean(self):
        """
        Validate that the email is from ASTU domain and properly formatted.
        """
        super().clean()
        
        if not re.match(r'^[a-zA-Z0-9_.+-]+@astu\.edu\.et$', self.university_email):
            raise ValidationError(
                _("Only valid @astu.edu.et email addresses are allowed.")
            )
    
    def __str__(self):
        return f"{self.username} ({self.university_email})"

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['university_email']),
            models.Index(fields=['username']),
            models.Index(fields=['is_active']),
        ]

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name