from django.contrib import admin

from .models import Admin as AdminUser
from .models import Customer, CustomerSupport
from .models import User as CustomUser

admin.site.register(CustomUser)
admin.site.register(Customer)
admin.site.register(CustomerSupport)
admin.site.register(AdminUser)
