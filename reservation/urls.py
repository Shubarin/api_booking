from django.conf.urls import url
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'reservation'

schema_view = get_schema_view(
    openapi.Info(
        title='Reserv API',
        default_version='v1',
        description='Для работы с системой требуется авторизация (токен). '
                    'Получите его перед выполнением запросов',
        terms_of_service='https://www.google.com/policies/terms/',
        contact=openapi.Contact(email='kirill.shubarin@gmail.com'),
        license=openapi.License(name='BSD License'),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    url(r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc'),
]

router = DefaultRouter()
router.register('reservations', views.ReservationViewSet,
                basename='ReservationView')
router.register('rooms', views.RoomViewSet, basename='RoomsView')
router.register('users', views.UserViewSet, basename='UserView')

urlpatterns += [
    path('', views.index, name='index'),
    path('api/v1/', include(router.urls)),
    path('room/<slug:slug>/', views.room_reservations, name='room'),
    path('new/', views.new_reservation, name="new_reservation"),
    path('<str:username>/', views.profile, name='profile'),
    path('<str:username>/<int:reservation_id>/', views.reservation_view,
         name='reservation'),
    path(
        '<str:username>/<int:reservation_id>/edit/',
        views.reservation_edit,
        name='reservation_edit'
    ),
    path('api/v1/api-token-auth/', obtain_auth_token),

]
