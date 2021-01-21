from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Building(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='Здание')

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=255,
                            unique=True,
                            verbose_name='Название рабочего места'
                            )
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(max_length=400)
    building = models.ForeignKey(Building,
                                 on_delete=models.CASCADE,
                                 related_name='room'
                                 )

    class Meta:
        ordering = ['building', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'building'], name='unique_room')
        ]

    def __str__(self):
        return self.name


class Reservation(models.Model):
    room = models.ForeignKey(Room,
                             on_delete=models.CASCADE,
                             related_name='reservation',
                             verbose_name='Рабочее место',
                             )
    datetime_from = models.DateTimeField('Начало бронирования')
    datetime_to = models.DateTimeField('Окончание бронирования')
    created = models.DateTimeField('Дата бронирования',
                                   auto_now_add=True)
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               verbose_name='Клиент',
                               )

    class Meta:
        ordering = ['-datetime_from', '-datetime_to', 'room']
        indexes = [
            models.Index(fields=['-datetime_from', '-datetime_to', ]),
            models.Index(fields=['room', ]),
        ]

    def full_clean(self, exclude=None, validate_unique=True):
        # Чтобы не искать пересечения по всем записям, сначала фильтруем
        # только по интересующему нас помещению
        if not self.datetime_from:
            raise ValidationError(
                {'datetime_from': ('Формат не соответствует ISO')})
        if not self.datetime_to:
            raise ValidationError(
                {'datetime_to': ('Формат не соответствует ISO')})
        room_reservation = Reservation.objects.filter(room=self.room)
        # Проверяем, что начало бронирования не попадает в занятый интервал
        from_intersects = room_reservation.filter(
            datetime_from__lte=self.datetime_from,
            datetime_to__gte=self.datetime_from
        ).count()
        # Проверяем, что окончание бронирования не попадает в занятый интервал
        to_intersects = room_reservation.filter(
            datetime_from__lte=self.datetime_to,
            datetime_to__gte=self.datetime_to
        ).count()
        # Проверяем, что новый интервал не включает в себя уже занятый интервал
        includes_interval = room_reservation.filter(
            datetime_from__gte=self.datetime_from,
            datetime_to__lte=self.datetime_to
        ).count()
        incorrect_interval = self.datetime_to <= self.datetime_from
        if from_intersects:
            raise ValidationError(
                {'datetime_from': ('Выбранное время занято. '
                                   'Выберите более позднее время '
                                   'для начала бронирования.')
                 }
            )
        if to_intersects:
            raise ValidationError(
                {'datetime_to': ('Выбранное время занято. '
                                 'Выберите более раннее время '
                                 'для окончания бронирования.')
                 }
            )
        if includes_interval:
            raise ValidationError({'datetime_to': ('Выбранное время занято.')})
        if incorrect_interval:
            msg_error = 'Некорректный промежуток бронирования. ' \
                        'Время окончания раньше времени начала'
            raise ValidationError(
                {'datetime_to': (msg_error), 'datetime_from': (msg_error)}
            )

    def __str__(self):
        return f'{self.room}: {self.datetime_from}-{self.datetime_to}. ' \
               f'{self.author} ({self.created})'
