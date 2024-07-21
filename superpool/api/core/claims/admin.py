from core.claims.models import Claim
from django.contrib import admin


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    pass
