from django.contrib import admin
from .models import RevokedAccessToken, UserToken


admin.site.register(RevokedAccessToken)
admin.site.register(UserToken)
