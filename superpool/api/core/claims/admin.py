from django.contrib import admin

from core.claims.models import Claim


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    pass
