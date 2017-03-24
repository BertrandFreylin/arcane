
from django.conf.urls import url
# from django.contrib import admin
from matcher import views

urlpatterns = [
    # url(r'^admin/', admin.site.urls),
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^export_csv', views.export_csv, name='export_csv'),
]
