import datetime

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from .filters import RoomFilterBackend
from .forms import ReservationForm
from .models import Reservation, Room, User
from .permissions import IsAuthorOrReadOnly
from .serializers import ReservationSerializer, RoomSerializer, UserSerializer

RECORDS_ON_THE_PAGE = 10


def index(request):
    reservations = Reservation.objects.all()
    paginator = Paginator(reservations, RECORDS_ON_THE_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'paginator': paginator,
        'page': page
    }
    return render(request, 'index.html', context)


def room_reservations(request, slug):
    room = get_object_or_404(Room, slug=slug)
    reservations = room.reservation.all()
    paginator = Paginator(reservations, RECORDS_ON_THE_PAGE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'paginator': paginator,
        'room': room,
        'page': page
    }
    return render(request, 'room.html', context)


@login_required
def new_reservation(request):
    form = ReservationForm(request.POST or None)
    if form.is_valid():
        reservation = form.save(commit=False)
        reservation.author = request.user
        reservation.save()
        return redirect('reservation:index')

    return render(request, 'reservation_new.html', {'form': form})


def profile(request, username):
    user = get_object_or_404(User.objects, username=username)
    reservation_list = Reservation.objects.filter(author=user)
    user_reservation_count = len(reservation_list)
    paginator = Paginator(reservation_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'profile_user': user,
        'user_reservation_count': user_reservation_count,
        'page': page
    }
    return render(request, 'profile.html', context)


@login_required
def reservation_view(request, username, reservation_id):
    user = get_object_or_404(User.objects, username=username)
    reservation = Reservation.objects.get(id__exact=reservation_id)
    user_reservation_count = Reservation.objects.filter(author=user).count()
    context = {
        'profile_user': user,
        'user_reservation_count': user_reservation_count,
        'reservation': reservation,
    }

    return render(request, 'reservation.html', context)


@login_required
def reservation_edit(request, username, reservation_id):
    current_user = request.user
    reservation = get_object_or_404(Reservation, id=reservation_id,
                                    author__username=username)
    reservation_author_user = reservation.author
    if current_user != reservation_author_user:
        return redirect('reservation:index')

    form = ReservationForm(request.POST or None, instance=reservation)
    if form.is_valid():
        form.save()
        return redirect('reservation:index')

    return render(request, 'reservation_new.html', {'form': form,
                                                    'action_text': 'Редактировать'})


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Бронирует рабочее место по id с datetime_from по datetime_to
        """
        return super(ReservationViewSet, self).create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Удаляет бронь по id.
        Пользователь, не являющийся автором брони, не может её удалять.
        """
        return super(ReservationViewSet, self).destroy(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Возвращает список всех имеющихся броней в системе.
        """
        return super(ReservationViewSet, self).list(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Вносит частичные обновления в бронь по id.
        Пользователь, не являющийся автором брони, не может её изменять.
        """
        return super(ReservationViewSet, self).partial_update(request, *args,
                                                              **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Выводит детальную информацию о бронировании по id
        """
        return super(ReservationViewSet, self).retrieve(request, *args,
                                                        **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Вносит обновления в бронь по id.
        Пользователь, не являющийся автором брони, не может её изменять.
        """
        return super(ReservationViewSet, self).update(request, *args, **kwargs)


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filter_class = RoomFilterBackend

    def create(self, request, *args, **kwargs):
        """
        Только пользователи, имеющие доступ к панели администратора,
        могут создавать новые рабочие места.
        """
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super(RoomViewSet, self).create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Только пользователи, имеющие доступ к панели администратора,
        могут удалять рабочие места.
        """
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super(RoomViewSet, self).destroy(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        datetime_from - опционально выбирает время начала выборки
        datetime_to - опционально выбирает время окончания выборки
        INPUT EXAMPLE: 2021-01-20 23:00:00
        Без параметров вернется список всех рабочих мест.
	    Если есть параметры, то вернется список рабочих мест,
	    свободных в указанный временной промежуток.
        """
        try:
            # получаем параметры запроса, если они невалидны шлем статус 400
            datetime_from = self.request.query_params.get('datetime_from', None)
            if datetime_from:
                datetime_from = datetime.datetime.fromisoformat(datetime_from)

            datetime_to = self.request.query_params.get('datetime_to', None)
            if datetime_to:
                datetime_to = datetime.datetime.fromisoformat(datetime_to)
                if datetime_to <= datetime_from:
                    raise ValueError(
                        'Перепутаны местами начало и конец периода')
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if not datetime_from or not datetime_to:
            queryset = Room.objects.all()
            serializer = RoomSerializer(queryset, many=True)
            return Response(serializer.data)
        queryset = Reservation.objects.filter(datetime_from__gte=datetime_from,
                                              datetime_to__lte=datetime_to)
        rooms = queryset.values_list('room', flat=True)
        queryset = Room.objects.exclude(id__in=set(rooms))
        serializer = RoomSerializer(queryset, many=True)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Только пользователи, имеющие доступ к панели администратора,
        могут изменять рабочие места.
        """
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super(RoomViewSet, self).partial_update(request, *args, **kwargs)

    def retrieve(self, request, pk=None, *args, **kwargs):
        """
        просмотра списка бронирований по id рабочего места
        """
        room = get_object_or_404(Room, pk=pk)
        queryset = room.reservation.all()
        serializer = ReservationSerializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Только пользователи, имеющие доступ к панели администратора,
        могут изменять рабочие места.
        """
        if not request.user.is_staff:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super(RoomViewSet, self).update(request, *args, **kwargs)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
