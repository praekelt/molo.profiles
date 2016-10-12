import random

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login, logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.http.request import QueryDict
from django.http.response import HttpResponseForbidden
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView, UpdateView

from molo.core.models import SiteLanguage, SiteSettings
from molo.profiles import forms
from molo.profiles.models import SecurityAnswer, SecurityQuestion
from molo.profiles.models import UserProfile, UserProfilesSettings


def get_pages(request, qs, locale):
    language = SiteLanguage.objects.filter(locale=locale).first()
    site_settings = SiteSettings.for_site(request.site)
    if site_settings.show_only_translated_pages:
        if language and language.is_main_language:
            return [a for a in qs.live()]
        else:
            pages = []
            for a in qs:
                translation = a.get_translation_for(locale)
                if translation:
                    pages.append(translation)
            return pages
    else:
        if language and language.is_main_language:
            return [a for a in qs.live()]
        else:
            pages = []
            for a in qs:
                translation = a.get_translation_for(locale)
                if translation:
                    pages.append(translation)
                elif a.live:
                    pages.append(a)
            return pages


class RegistrationView(FormView):
    """
    Handles user registration
    """
    form_class = forms.RegistrationForm
    template_name = "profiles/register.html"

    def form_valid(self, form):
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        mobile_number = form.cleaned_data["mobile_number"]
        user = User.objects.create_user(username=username, password=password)
        user.profile.mobile_number = mobile_number
        if form.cleaned_data["email"]:
            user.email = form.cleaned_data["email"]
            user.save()
        user.profile.save()

        for index, question in enumerate(self.questions):
            answer = form.cleaned_data["question_%s" % index]
            SecurityAnswer.objects.create(
                user=user.profile,
                question=question,
                answer=answer
            )

        authed_user = authenticate(username=username, password=password)
        login(self.request, authed_user)
        return HttpResponseRedirect(form.cleaned_data.get("next", "/"))

    def get_form_kwargs(self):
        kwargs = super(RegistrationView, self).get_form_kwargs()
        queryset = SecurityQuestion.objects.live().filter(
            languages__language__is_main_language=True)
        self.questions = get_pages(
            self.request, queryset, self.request.LANGUAGE_CODE)
        kwargs["questions"] = self.questions
        return kwargs


class RegistrationDone(FormView):
    """
    Enables updating of the user's date of birth
    """
    form_class = forms.DateOfBirthForm
    template_name = 'profiles/done.html'

    def form_valid(self, form):
        profile = self.request.user.profile
        profile.date_of_birth = form.cleaned_data['date_of_birth']
        profile.save()
        return HttpResponseRedirect(form.cleaned_data.get('next', '/'))


def logout_page(request):
    logout(request)
    return HttpResponseRedirect(request.GET.get('next', '/'))


class MyProfileView(TemplateView):
    """
    Enables viewing of the user's profile in the HTML site, by the profile
    owner.
    """
    template_name = 'profiles/viewprofile.html'


class MyProfileEdit(UpdateView):
    """
    Enables editing of the user's profile in the HTML site
    """
    model = UserProfile
    form_class = forms.EditProfileForm
    template_name = 'profiles/editprofile.html'
    success_url = reverse_lazy('molo.profiles:view_my_profile')

    def get_initial(self):
        initial = super(MyProfileEdit, self).get_initial()
        initial.update({'email': self.request.user.email})
        return initial

    def form_valid(self, form):
        super(MyProfileEdit, self).form_valid(form)
        self.request.user.email = form.cleaned_data['email']
        self.request.user.save()
        return HttpResponseRedirect(
            reverse('molo.profiles:view_my_profile'))

    def get_object(self, queryset=None):
        return self.request.user.profile


class ProfilePasswordChangeView(FormView):
    form_class = forms.ProfilePasswordChangeForm
    template_name = 'profiles/change_password.html'

    def form_valid(self, form):
        user = self.request.user
        if user.check_password(form.cleaned_data['old_password']):
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            return HttpResponseRedirect(
                reverse('molo.profiles:view_my_profile'))
        messages.error(
            self.request,
            _('The old password is incorrect.')
        )
        return render(self.request, self.template_name,
                      {'form': form})


class ForgotPasswordView(FormView):
    form_class = forms.ForgotPasswordForm
    template_name = "profiles/forgot_password.html"

    def form_valid(self, form):
        error_message = "The username and security question(s) combination " \
                        + "do not match."
        profile_settings = UserProfilesSettings.for_site(self.request.site)

        if "forgot_password_attempts" not in self.request.session:
            self.request.session["forgot_password_attempts"] = \
                profile_settings.password_recovery_retries

        # max retries exceeded
        if self.request.session["forgot_password_attempts"] <= 0:
            form.add_error(
                None,
                _("Too many attempts. Please try again later.")
            )
            return self.render_to_response({'form': form})

        username = form.cleaned_data["username"]
        try:
            user = User.objects.get_by_natural_key(username)
        except User.DoesNotExist:
            # add non_field_error
            form.add_error(None, _(error_message))
            self.request.session["forgot_password_attempts"] -= 1
            return self.render_to_response({'form': form})

        if not user.is_active:
            # add non_field_error
            form.add_error(None, _(error_message))
            self.request.session["forgot_password_attempts"] -= 1
            return self.render_to_response({'form': form})

        # check security question answers
        answer_checks = []
        for i in range(profile_settings.num_security_questions):
                user_answer = form.cleaned_data["question_%s" % (i,)]
                saved_answer = user.profile.securityanswer_set.get(
                    user=user.profile,
                    question=self.security_questions[i]
                )
                answer_checks.append(
                    saved_answer.check_answer(user_answer)
                )

        # redirect to reset password page if username and security
        # questions were matched
        if all(answer_checks):
            token = default_token_generator.make_token(user)
            q = QueryDict(mutable=True)
            q["user"] = username
            q["token"] = token
            reset_password_url = "{0}?{1}".format(
                reverse("molo.profiles:reset_password"), q.urlencode()
            )
            return HttpResponseRedirect(reset_password_url)
        else:
            form.add_error(None, _(error_message))
            self.request.session["forgot_password_attempts"] -= 1
            return self.render_to_response({'form': form})

    def get_form_kwargs(self):
        # add security questions for form field generation
        kwargs = super(ForgotPasswordView, self).get_form_kwargs()
        queryset = SecurityQuestion.objects.live().filter(
            languages__language__is_main_language=True
        )
        self.security_questions = get_pages(
            self.request, queryset, self.request.LANGUAGE_CODE)
        random.shuffle(self.security_questions)
        profile_settings = UserProfilesSettings.for_site(self.request.site)
        kwargs["questions"] = self.security_questions[
            :profile_settings.num_security_questions
        ]
        return kwargs


class ResetPasswordView(FormView):
    form_class = forms.ResetPasswordForm
    template_name = "profiles/reset_password.html"

    def form_valid(self, form):
        username = form.cleaned_data["username"]
        token = form.cleaned_data["token"]

        try:
            user = User.objects.get_by_natural_key(username)
        except User.DoesNotExist:
            return HttpResponseForbidden()

        if not user.is_active:
            return HttpResponseForbidden()

        if not default_token_generator.check_token(user, token):
            return HttpResponseForbidden()

        password = form.cleaned_data["password"]
        confirm_password = form.cleaned_data["confirm_password"]

        if password != confirm_password:
            form.add_error(None,
                           _("The two PINs that you entered do not match. "
                             "Please try again."))
            return self.render_to_response({"form": form})

        user.set_password(password)
        user.save()
        self.request.session.flush()

        return HttpResponseRedirect(
            reverse("molo.profiles:reset_password_success")
        )

    def render_to_response(self, context, **response_kwargs):
        username = self.request.GET.get("user")
        token = self.request.GET.get("token")

        if not username or not token:
            return HttpResponseForbidden()

        context["form"].initial.update({
            "username": username,
            "token": token
        })

        return super(ResetPasswordView, self).render_to_response(
            context, **response_kwargs
        )
