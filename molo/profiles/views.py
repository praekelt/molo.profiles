from molo.profiles.forms import RegistrationForm
from molo.profiles.forms import EditProfileForm, ProfilePasswordChangeForm
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


@csrf_protect
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            user.profile.date_of_birth = form.cleaned_data['date_of_birth']
            user.profile.save()
            return HttpResponseRedirect(reverse('home_page'))
        return render(request, 'registration/register.html', {'form': form})
    form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


def register_success(request):
    return HttpResponseRedirect(reverse('home_page'))


def logout_page(request):
    logout(request)
    return HttpResponseRedirect(reverse('home_page'))


def home(request):
    return render(request, 'core/main.html')


class MyProfileView(TemplateView):
    """
    Enables viewing of the user's profile in the HTML site, by the profile
    owner.
    """
    template_name = 'templates/viewprofile.html'


class MyProfileEdit(FormView):
    """
    Enables editing of the user's profile in the HTML site
    """
    form_class = EditProfileForm
    template_name = 'templates/editprofile.html'

    def form_valid(self, form):
        user = self.request.user
        profile = user.profile
        profile.alias = form.cleaned_data['alias']
        profile.save()
        return HttpResponseRedirect(reverse('view_my_profile'))


class ProfilePasswordChangeView(FormView):
    form_class = ProfilePasswordChangeForm
    template_name = 'templates/change_password.html'

    def form_valid(self, form):
        user = self.request.user
        if user.check_password(form.cleaned_data['old_password']):
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            return HttpResponseRedirect(reverse('view_my_profile'))
        messages.error(
            self.request,
            _('The Old password is incorrect.')
        )
        return render(self.request, 'templates/change_password.html',
                      {'form': form})
