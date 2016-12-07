from molo.profiles.admin import FrontendUsersModelAdmin, AdminUsersModel
from wagtailmodeladmin.options import wagtailmodeladmin_register


wagtailmodeladmin_register(FrontendUsersModelAdmin)
wagtailmodeladmin_register(AdminUsersModel)
