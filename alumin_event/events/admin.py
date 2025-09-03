from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(Event)
admin.site.register(AgendaItem)
admin.site.register(FormDefinition)
admin.site.register(DynamicField)
admin.site.register(FormSubmission)
admin.site.register(Beverage)
admin.site.register(EventRegistration)
admin.site.register(SubmissionFile)
admin.site.register(Payment)
admin.site.register(Order)
admin.site.register(Student)