from django.contrib import admin

from .models import Customer
from .models import Admin as AdminUser
from .models import User as CustomUser
from .models import CustomerSupport

admin.site.register(CustomUser)
admin.site.register(Customer)
admin.site.register(CustomerSupport)
admin.site.register(AdminUser)
