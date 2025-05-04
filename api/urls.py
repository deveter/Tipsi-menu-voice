from django.urls import path
from .views import EnviarCartaView,TranscribeView

urlpatterns = [
    path('transcribe/', TranscribeView.as_view()),
    path('enviar-carta/', EnviarCartaView.as_view()),
]
