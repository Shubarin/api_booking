from django.contrib import admin

from .models import Building, Reservation, Room


class ReserveAdmin(admin.ModelAdmin):
    list_display = ("pk", "room", "datetime_from",
                    "datetime_to", "author", "created")
    search_fields = ("room",)
    list_filter = ("datetime_from",)
    empty_value_display = "-пусто-"


class RoomAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "building",)
    search_fields = ("name",)
    list_filter = ("building",)
    empty_value_display = "-пусто-"


admin.site.register(Reservation, ReserveAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Building)
