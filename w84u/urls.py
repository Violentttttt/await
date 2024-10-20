from django.urls import include, path
from rest_framework import routers
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from . import views , authentication

from .views import CustomUserViewSet, MarkerViewSet, MarkerHistoryViewSet, MatchViewSet, MessageViewSet, \
    CustomTokenRefreshView
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

                  path('api/v1/save_locations/', views.SaveLocationsView.as_view(), name='save_locations'),
                  path('api/v1/save_info/', views.Save_infoView.as_view(), name='save_info'),
                  path('api/v1/', include(router.urls)),
                  path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
                  path('api/v1/token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
                  # path('api/v1/token/verify/', views.TokenVerifyView.as_view(), name='token_verify_for_auto_login'), теперь использую только 1 верифай - следующий
                  path('api/v1/token/verify/app/', views.Verify_for_app.as_view(), name='token_verify_for_app'),
                  path('api/v1/account/', views.AccountView.as_view(), name='account'),
                  path('api/v1/history/', views.HistoryAPIView.as_view(), name='history'),
                  path('api/v1/register/', views.RegisterAPIView.as_view(), name='api_register'),
                  path('api/v1/login/', views.LoginAPIView.as_view(), name='api_login'),
                  path('api/v1/logout/', views.LogoutAPIView.as_view(), name='api_logout'),
                  path('api/v1/wstoken/', views.WSAPIView.as_view(), name='wstoken'),
                  path('api/v1/account/optionalinfo/', views.OptionalInfoView.as_view(), name='optionalinfo'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
