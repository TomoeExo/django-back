from django.contrib import admin

# Register your models here.
from api import models as api_models

admin.site.register(api_models.User)
admin.site.register(api_models.UserDetails)
admin.site.register(api_models.Subscription)
admin.site.register(api_models.Chat)
admin.site.register(api_models.Message)
admin.site.register(api_models.Workout)
admin.site.register(api_models.WorkoutCompleted)
admin.site.register(api_models.Goal)