from concurrent.futures import ThreadPoolExecutor
import os
import tempfile
import json
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

# Configura logging
logger = logging.getLogger(__name__)

# Carga la API key de OpenAI
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / '.env')
openai.api_key = os.getenv("OPENAI_API_KEY")

class TranscribeView(APIView):
    parser_classes = [MultiPartParser]

    def transcribir_archivo(self, audio_file):
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_audio:
                for chunk in audio_file.chunks():
                    temp_audio.write(chunk)
                temp_audio.flush()

                with open(temp_audio.name, "rb") as f:
                    transcript = openai.Audio.transcribe(
                        model="whisper-1",
                        file=f,
                        response_format="text",
                        language="es"
                    ).strip()
                    logger.info(f"📝 Transcripción Whisper: {transcript}")
                    return transcript
        finally:
            if os.path.exists(temp_audio.name):
                os.remove(temp_audio.name)

    def post(self, request, *args, **kwargs):
        audio_files = request.FILES.getlist('audios')
        if not audio_files:
            return Response({"error": "No se recibió ningún archivo de audio"}, status=400)

        with ThreadPoolExecutor() as executor:
            transcripciones = list(executor.map(self.transcribir_archivo, audio_files))

        transcript = "\n".join(transcripciones)

        prompt = f"""
Convierte este audio transcrito (de un hostelero dictando su carta) en una lista JSON con los campos:
- familia
- producto (son nombres de productos de restaurantes)
- precio (en número, sin símbolo €)
- formato: tapa, ración, plato… o "Único" si no se indica

Ejemplo:
[
  {{
    "familia": "Entrantes",
    "producto": "Croquetas",
    "precio": 2,
    "formato": "Único"
  }}
]

Texto: {transcript}
"""

        try:
            gpt_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # ⬅️ más rápido que GPT-4
                messages=[
                    {"role": "system", "content": "Eres un asistente que convierte listas habladas de cartas de restaurante en JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            structured = gpt_response["choices"][0]["message"]["content"].strip()

        except Exception as e:
            logger.exception("❌ Error al llamar a GPT")
            structured = "[]"

        return Response({
            "transcription": transcript,
            "structured": structured
        })

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
