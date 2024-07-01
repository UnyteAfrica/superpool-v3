from django.contrib import admin

from .models import Policy, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    pass
