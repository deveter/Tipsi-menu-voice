<template> 
  <div class="recorder">
    <button @click="startRecording" :disabled="recording">🎤 Empezar</button>
    <button @click="stopRecording" :disabled="!recording">🛑 Parar</button>

    <div v-if="audioUrl" class="preview">
      <p>✅ Grabación completada:</p>
      <audio :src="audioUrl" controls></audio>
      <button @click="sendAudio">➡️ Enviar a Tipsi</button>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      mediaRecorder: null,
      audioChunks: [],
      audioBlob: null,
      audioUrl: null,
      recording: false,
    };
  },
  methods: {
    async startRecording() {
      const beep = new Audio('/static/beep.mp3');
      await beep.play();

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.mediaRecorder = new MediaRecorder(stream);
      this.audioChunks = [];

      this.mediaRecorder.ondataavailable = (e) => {
        this.audioChunks.push(e.data);
      };

      this.mediaRecorder.onstop = () => {
        this.audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        this.audioUrl = URL.createObjectURL(this.audioBlob);
        this.$forceUpdate();
      };

      this.mediaRecorder.start();
      this.recording = true;
    },

    stopRecording() {
      if (this.mediaRecorder && this.recording) {
        this.mediaRecorder.stop();
        this.recording = false;
      }
    },

    async sendAudio() {
      const formData = new FormData();
      formData.append('audio', this.audioBlob, 'grabacion.webm');

      const baseUrl =
        import.meta.env.MODE === 'development'
          ? 'http://localhost:8000'
          : window.location.origin;

      this.$emit('procesandoIniciado');

      try {
        const res = await fetch(`${baseUrl}/api/transcribe/`, {
          method: 'POST',
          body: formData,
        });

        if (!res.ok) {
          const text = await res.text();
          console.error('⚠️ Error del servidor:', text);
          this.$emit('procesandoFinalizado');
          throw new Error('Error al transcribir');
        }

        const result = await res.json();
        this.$emit('transcriptionReceived', result);
        this.reset(); // 🔁 Reinicia después de enviar con éxito
      } catch (error) {
        console.error('Error al enviar el audio:', error);
        this.$emit('procesandoFinalizado');
      }
    },

    reset() {
      this.audioBlob = null;
      this.audioUrl = null;
      this.audioChunks = [];
      this.mediaRecorder = null;
      this.recording = false;
    }
  },
};
</script>

<style scoped>
.recorder {
  padding: 1rem;
  text-align: center;
}
button {
  margin: 0.5rem;
}
.preview {
  margin-top: 1rem;
}
</style>
