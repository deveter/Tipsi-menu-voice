import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import openai
import pandas as pd
from api.email import enviar_email_brevo
import logging

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from django.core.mail import EmailMessage
from django.views.generic import View
from django.http import HttpResponse, Http404
from django.conf import settings

logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / '.env')
openai.api_key = os.getenv("OPENAI_API_KEY")

class TranscribeView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, *args, **kwargs):
        audio_files = request.FILES.getlist('audios')
        if not audio_files:
            return Response({"error": "No se recibió ningún archivo de audio"}, status=400)

        transcripciones = []

        try:
            for audio_file in audio_files:
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_audio:
                    for chunk in audio_file.chunks():
                        temp_audio.write(chunk)
                    temp_audio.flush()

                    with open(temp_audio.name, "rb") as f:
                        transcript_response = openai.Audio.transcribe(
                            model="whisper-1",
                            file=f,
                            response_format="text"
                        )
                        transcripciones.append(transcript_response)

                os.remove(temp_audio.name)

            transcript = "\n".join(transcripciones)

            prompt = f"""
Convierte este texto hablado en una lista JSON con los siguientes campos:
- familia: categoría del producto
- producto: nombre del producto
- precio: en número (sin símbolo de €)
- formato: si se menciona 'tapa', 'ración', 'plato' u otro formato, indícalo. Si no se menciona, usa "Único" como valor por defecto.

Ejemplo de salida:
[
  {{
    "familia": "Entrantes",
    "producto": "Croquetas",
    "precio": 2,
    "formato": "Único"
  }},
  {{
    "familia": "Entrantes",
    "producto": "Calamares fritos",
    "precio": 5,
    "formato": "ración"
  }}
]

Texto: {transcript}
"""

            gpt_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un asistente que convierte listas habladas de cartas de restaurante en tablas JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            structured = gpt_response["choices"][0]["message"]["content"]

            return Response({
                "transcription": transcript,
                "structured": structured
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)

class EnviarCartaView(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        nombre = request.data.get("nombre_restaurante")
        email = request.data.get("email")
        carta = request.data.get("carta")

        if not nombre or not email or not carta:
            return Response({"error": "Faltan datos"}, status=400)

        try:
            df = pd.DataFrame(carta)
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                excel_path = tmp.name
                df.to_excel(excel_path, index=False)

            asunto = f"📋 Nueva carta enviada por {nombre}"
            cuerpo = f"El restaurante '{nombre}' con email '{email}' ha enviado su carta adjunta en Excel."

            enviar_email_brevo(
                destinatario="ppinar@tipsitpv.com",
                asunto=asunto,
                cuerpo=cuerpo,
                adjunto=excel_path
            )

            return Response({"message": "Carta enviada correctamente"})

        except Exception as e:
            logger.exception("❌ Error al enviar el email:")
            return Response({"error": str(e)}, status=500)

class FrontendAppView(View):
    def get(self, request):
        index_path = os.path.join(settings.BASE_DIR, 'staticfiles', 'index.html')
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read())
        else:
            raise Http404("index.html no encontrado en STATIC_ROOT")
