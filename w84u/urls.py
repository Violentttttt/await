from django.urls import include, path
from rest_framework import routers
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from . import views

from .views import CustomUserViewSet, MarkerViewSet, MarkerHistoryViewSet, MatchViewSet, MessageViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

router = routers.DefaultRouter()
router.register(r'users', views.CustomUserViewSet, basename='users')
router.register(r'marker', views.MarkerViewSet, basename='marker')
router.register(r'markerhistory', views.MarkerHistoryViewSet, basename='markerhistory')
router.register(r'maybematch', views.MaybeMatchViewSet, basename='maybematch')
router.register(r'match', views.MatchViewSet, basename='match')
router.register(r'message', views.MessageViewSet, basename='message')
router.register(r'session', views.SessionViewSet, basename='session')
router.register(r'optionalinfo', views.OptionalInfoViewSet, basename='optionalinfo')

urlpatterns = [
                  path('api/v1/maybematch', views.MaybeMatchAPIView.as_view(), name='maybematch'),
                  path('api/v1/match/', views.MatchView.as_view(), name='match'),

                  path('', views.main, name='all'),
                  path('register/', views.register, name='registration'),
                  path('login/', views.user_login, name='login'),
                  path('logout/', views.logout_user, name='logout'),
                  path('map/', views.map_view, name='map'),
                  path('api/v1/save_locations/', views.SaveLocationsView.as_view(), name='save_locations'),
                  path('api/v1/save_info/', views.Save_infoView.as_view(), name='save_info'),
                  path('api/v1/', include(router.urls)),
                  # path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
                  # path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
                  # path('api/v1/token/verify/', TokenVerifyView.as_view(), name='token_refresh'),
                  path('api/v1/world/', views.WorldView.as_view(), name='world'),
                  path('api/v1/account/', views.AccountView.as_view(), name='account'),

                  path('api/v1/account/optionalinfo/', views.OptionalInfoView.as_view(), name='optionalinfo'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
