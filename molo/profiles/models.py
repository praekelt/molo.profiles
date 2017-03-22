from django.contrib.auth import hashers
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _


from molo.core.models import TranslatablePageMixin, PreventDeleteMixin
from phonenumber_field.modelfields import PhoneNumberField
from wagtail.wagtailcore.models import Page, Site
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel, MultiFieldPanel, PageChooserPanel)


@register_setting
class UserProfilesSettings(BaseSetting):
    show_mobile_number_field = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Add mobile number field to registration"),
    )
    mobile_number_required = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Mobile number required"),
    )
    country_code = models.CharField(
        max_length=4,
        null=True, blank=True,
        verbose_name=_(
            "The country code that should be added to a user's number for "
            "this site"),
        help_text=_("For example: +27 for South Africa, +44 for England")
    )
    prevent_phone_number_in_username = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Prevent phone number in username / display name"),
    )

    show_email_field = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Add email field to registration")
    )
    email_required = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Email required")
    )

    prevent_email_in_username = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Prevent email in username / display name"),
    )

    show_security_question_fields = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Add security question fields to registration")
    )
    security_questions_required = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Security questions required")
    )
    num_security_questions = models.PositiveSmallIntegerField(
        default=1,
        verbose_name=_("Number of security questions asked for "
                       "password recovery")
    )
    password_recovery_retries = models.PositiveSmallIntegerField(
        default=5,
        verbose_name=_("Max number of password recovery retries before "
                       "lockout")
    )
    terms_and_conditions = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text=_('Choose a footer page')
    )
    activate_display_name = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Activate Display Name"),
    )
    capture_display_name = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Capture On Registration"),
    )
    display_name_required = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Display Name Required"),
    )
    activate_gender = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Activate Gender"),
    )
    capture_gender = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Capture On Registration"),
    )
    gender_required = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Gender Required"),
    )
    activate_dob = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Activate Date Of Birth"),
    )
    capture_dob = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Capture On Registration"),
    )
    dob_required = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Date Of Birth Required"),
    )
    activate_location = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Activate Location"),
    )
    capture_location = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Capture On Registration"),
    )
    location_required = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Location Required"),
    )
    activate_education_level = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Activate Education Level"),
    )
    capture_education_level = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Capture On Registration"),
    )
    activate_education_level_required = models.BooleanField(
        default=False,
        editable=True,
        verbose_name=_("Education Level Required"),
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel('show_mobile_number_field'),
                FieldPanel('mobile_number_required'),
                FieldPanel('country_code'),
                FieldPanel('prevent_phone_number_in_username'),
            ],
            heading="Mobile Number Settings", ),
        MultiFieldPanel(
            [
                FieldPanel('show_email_field'),
                FieldPanel('email_required'),
                FieldPanel('prevent_email_in_username'),
            ],
            heading="Email Settings", ),
        MultiFieldPanel(
            [
                FieldPanel("show_security_question_fields"),
                FieldPanel("security_questions_required"),
                FieldPanel("num_security_questions"),
                FieldPanel("password_recovery_retries"),
            ],
            heading="Security Question Settings", ),
        MultiFieldPanel(
            [
                PageChooserPanel('terms_and_conditions'),
            ],
            heading="Terms and Conditions on registration", ),
        MultiFieldPanel(
            [
                FieldPanel('activate_display_name'),
                FieldPanel('capture_display_name'),
                FieldPanel('display_name_required'),
            ],
            heading="Display Name", ),
        MultiFieldPanel(
            [
                FieldPanel('activate_gender'),
                FieldPanel('capture_gender'),
                FieldPanel('gender_required'),
            ],
            heading="Gender", ),
        MultiFieldPanel(
            [
                FieldPanel('activate_dob'),
                FieldPanel('capture_dob'),
                FieldPanel('dob_required'),
            ],
            heading="Date Of Birth", ),
        MultiFieldPanel(
            [
                FieldPanel('activate_location'),
                FieldPanel('capture_location'),
                FieldPanel('location_required'),
            ],
            heading="Location", ),
        MultiFieldPanel(
            [
                FieldPanel('activate_education_level'),
                FieldPanel('capture_education_level'),
                FieldPanel('activate_education_level_required'),
            ],
            heading="Education Level", )
    ]
    # TODO: mobile_number_required field shouldn't be shown
    # if show_mobile_number_field is False


class SecurityQuestion(TranslatablePageMixin, Page):

    class Meta:
        verbose_name = _("Security Question")

    def __str__(self):
        return self.title


SecurityQuestion.content_panels = [
    FieldPanel("title", classname="full title")
]
SecurityQuestion.promote_panels = []
SecurityQuestion.settings_panels = []


class SecurityQuestionIndexPage(Page, PreventDeleteMixin):
    parent_page_types = ['core.Main']
    subpage_types = ["SecurityQuestion"]


SecurityQuestionIndexPage.content_panels = [
    FieldPanel('title', classname='full title'),
]


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="profile", primary_key=True)
    date_of_birth = models.DateField(null=True)
    alias = models.CharField(
        max_length=128,
        blank=True,
        null=True)
    gender = models.CharField(
        max_length=128,
        blank=True,
        null=True)
    location = models.CharField(
        max_length=128,
        blank=True,
        null=True)
    education_level = models.CharField(
        max_length=128,
        blank=True,
        null=True)
    avatar = models.ImageField(
        'avatar',
        max_length=100,
        upload_to='users/profile',
        blank=True,
        null=True)

    mobile_number = PhoneNumberField(blank=True, null=True, unique=False)
    security_question_answers = models.ManyToManyField(
        SecurityQuestion,
        through="SecurityAnswer"
    )
    site = models.ForeignKey(Site, blank=True, null=True)


@receiver(post_save, sender=User)
def user_profile_handler(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile(user=instance)
        profile.save()


class SecurityAnswer(models.Model):
    user = models.ForeignKey(UserProfile)
    question = models.ForeignKey(SecurityQuestion)
    answer = models.CharField(max_length=150, null=False, blank=False)

    def set_answer(self, raw_answer):
        self.answer = hashers.make_password(raw_answer.strip().lower())

    def check_answer(self, raw_answer):
        def setter(raw_answer):
            self.set_answer(raw_answer)
            self.save(update_fields=["answer"])

        return hashers.check_password(
            raw_answer.strip().lower(),
            self.answer,
            setter
        )

    def save(self, *args, **kwargs):
        if not self.id:
            self.set_answer(self.answer)
        super(SecurityAnswer, self).save(*args, **kwargs)
