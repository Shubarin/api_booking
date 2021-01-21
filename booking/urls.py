from django.conf.urls import handler404, handler500
from django.contrib import admin
from django.contrib.flatpages import views
from django.urls import include, path

from booking import settings

handler404 = "reservation.views.page_not_found"  # noqa
handler500 = "reservation.views.server_error"  # noqa

urlpatterns = [
    path('about/', include('django.contrib.flatpages.urls')),
    path('about-us/', views.flatpage, {'url': '/about-us/'}, name='about'),
    path('terms/', views.flatpage, {'url': '/terms/'}, name='terms'),
    path('contacts/', views.flatpage, {'url': '/contacts/'}, name='contacts'),
    path('about-spec/', views.flatpage, {'url': '/about-spec/'},
         name='about-spec'),
    path('about-author/', views.flatpage, {'url': '/about-author/'},
         name='about-author'),
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('', include(('reservation.urls', 'reservation'),
                     namespace='reservation:index')),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns += (path("__debug__/", include(debug_toolbar.urls)),)