from import_export import resources
from django.contrib.auth.models import User
from import_export.fields import Field


class FrontendUsersResource(resources.ModelResource):
    # see dehydrate_ functions below
    date_of_birth = Field()
    alias = Field()
    mobile_number = Field()

    class Meta:
        model = User

        exclude = ('id', 'password', 'is_superuser', 'groups',
                   'user_permissions', 'is_staff')

        export_order = ('username', 'alias', 'first_name', 'last_name',
                        'date_of_birth', 'email', 'mobile_number', 'is_active',
                        'date_joined', 'last_login')

    # unfortunately Field's 'attribute' parameter does not work for these
    def dehydrate_date_of_birth(self, user):
        return user.profile.date_of_birth if hasattr(user, 'profile') else ''

    def dehydrate_alias(self, user):
        return user.profile.alias if hasattr(user, 'profile') else ''

    def dehydrate_mobile_number(self, user):
        return user.profile.mobile_number if hasattr(user, 'profile') else ''
