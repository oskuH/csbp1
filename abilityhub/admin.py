from django.contrib import admin

from . models import Person, Image, Chat, Message, Transaction, Deposit, Log

class PersonAdmin(admin.ModelAdmin):
    list_display = ["user", "credits", "description"]

admin.site.register(Person, PersonAdmin)

admin.site.register(Image)

admin.site.register(Chat)

admin.site.register(Message)

admin.site.register(Transaction)

admin.site.register(Deposit)

admin.site.register(Log)