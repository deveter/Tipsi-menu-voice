<template>
  <div>
    <div class="logo-container">
      <img src="./assets/tipsi-logo.png" alt="Tipsi Logo" class="logo" />
    </div>

    <div class="app">
      <h1>Dicta tu carta 🗣️</h1>

      <p class="ejemplo-label">Aquí tienes un ejemplo de cómo hacerlo:</p>
      <audio controls>
        <source src="/static/ejemplo.webm" type="audio/webm" />
        Tu navegador no soporta el elemento de audio.
      </audio>

      <AudioRecorder
        ref="grabador"
        @transcriptionReceived="handleTranscription"
        @procesandoIniciado="procesando = true"
        @procesandoFinalizado="procesando = false"
      />

      <div ref="tabla" v-if="structured.length" class="tabla-wrapper">
        <h2>Tabla generada:</h2>
        <table class="menu-table">
          <thead>
            <tr>
              <th>Familia</th>
              <th>Producto</th>
              <th>€</th>
              <th>❌</th>
            </tr>
          </thead>
          <tbody>
            <tr :class="{ incompleta: filaIncompleta === index }" v-for="(item, index) in structured" :key="index">
              <td>
                <td style="position: relative;">
                  <input
                    v-model="item.familia"
                    @input="updateSuggestions(index)"
                    @focus="showSuggestionsIndex = index"
                    @blur="hideSuggestions"
                  />
                  <ul
                    v-if="showSuggestionsIndex === index && filteredSuggestions.length"
                    class="suggestions"
                  >
                    <li
                      v-for="(suggestion, i) in filteredSuggestions"
                      :key="i"
                      @mousedown.prevent="selectSuggestion(index, suggestion)"
                    >
                      {{ suggestion }}
                    </li>
                  </ul>
                </td>
              </td>
              <td><textarea v-model="item.producto" rows="2" /></td>
              <td><input v-model="item.precio" /></td>
              <td><button class="button-cross" @click="removeRow(index)">❌</button></td>
            </tr>
          </tbody>
        </table>
        <div v-if="filaIncompleta !== null" class="error-message">
          ❌ Por favor, completa todos los campos de la fila {{ filaIncompleta + 1 }} antes de continuar.
        </div>
      </div>
    </div>

    <div v-if="structured.length" class="fixed-buttons">
      <button class="left" @click="addRow">➕ Añadir fila</button>
      <button class="right" @click="submitFinalData">✅ Enviar</button>
    </div>

    <div v-if="showForm" class="modal-overlay">
      <div class="modal-envio">
        <h3>📤 Enviar carta</h3>
        <div class="form-group">
          <label>Nombre del restaurante</label>
          <input v-model="formData.nombre_restaurante" placeholder="Ej: Casa Pepe" />
        </div>
        <div class="form-group">
          <label>Email del hostelero</label>
          <input v-model="formData.email" placeholder="ejemplo@correo.com" />
        </div>
        <div class="modal-buttons">
          <button class="confirm" @click="confirmarEnvio">Confirmar</button>
          <button class="cancel" @click="cancelarEnvio">Cancelar</button>
        </div>
      </div>
    </div>

    <div v-if="procesando" class="modal-overlay">
      <div class="modal">
        <h3>Procesando los datos por Tipsi...</h3>
      </div>
    </div>

    <div v-if="enviandoCarta" class="modal-overlay">
      <div class="modal">
        <h3>Enviando carta a Tipsi...</h3>
      </div>
    </div>

    <div v-if="enviadoConExito" class="modal-overlay">
      <div class="modal">
        <h3>🎉 Carta enviada con éxito</h3>
      </div>
    </div>
  </div>
</template>

<script>
import AudioRecorder from './components/AudioRecorder.vue';

export default {
  components: { AudioRecorder },
  data() {
    return {
      structured: [],
      enviadoConExito: false,
      filaIncompleta: null,
      showForm: false,
      procesando: false,
      showSuggestionsIndex: null,
      enviandoCarta: false,
      filteredSuggestions: [],
      formData: {
        nombre_restaurante: '',
        email: '',
      }
    };
  },
  methods: {
    handleTranscription(response) {
      this.procesando = false;
      try {
        const parsed = typeof response.structured === 'string'
          ? JSON.parse(response.structured)
          : response.structured;

        this.structured = parsed.map(item => ({
          familia: this.capitalize(item.familia),
          producto: this.capitalize(item.producto),
          precio: item.precio
        }));

        this.$nextTick(() => {
          this.$refs.tabla.scrollIntoView({ behavior: 'smooth' });
        });
      } catch (e) {
        console.error('Error al parsear el JSON:', e);
      }
    },
    capitalize(text) {
      if (!text || typeof text !== 'string') return text;
      return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
    },
    addRow() {
      this.structured.unshift({ familia: '', producto: '', precio: '' });
      this.$nextTick(() => {
        this.$refs.tabla.scrollIntoView({ behavior: 'smooth' });
      });
    },
    removeRow(index) {
      this.structured.splice(index, 1);
    },
    updateSuggestions(index) {
      const input = this.structured[index].familia.toLowerCase();
      const uniqueFamilies = [...new Set(this.structured.map(i => i.familia))];
      this.filteredSuggestions = uniqueFamilies.filter(f =>
        f.toLowerCase().startsWith(input) && f.toLowerCase() !== input
      );
      this.showSuggestionsIndex = index;
    },
    selectSuggestion(index, value) {
      this.structured[index].familia = value;
      this.filteredSuggestions = [];
      this.showSuggestionsIndex = null;
    },
    hideSuggestions() {
      setTimeout(() => {
        this.filteredSuggestions = [];
        this.showSuggestionsIndex = null;
      }, 200);
    },
    submitFinalData() {
      this.filaIncompleta = null;

      for (let i = 0; i < this.structured.length; i++) {
        const item = this.structured[i];
        if (!item.familia.trim() || !item.producto.trim() || !item.precio.toString().trim()) {
          this.filaIncompleta = i;

          this.$nextTick(() => {
            const row = document.querySelectorAll('.menu-table tbody tr')[i];
            if (row) row.scrollIntoView({ behavior: 'smooth', block: 'center' });
          });

          return;
        }
      }

      this.showForm = true;
    },
    cancelarEnvio() {
      this.showForm = false;
    },
    async confirmarEnvio() {
      const { nombre_restaurante, email } = this.formData;

      if (!nombre_restaurante.trim() || !email.trim()) {
        alert('Por favor, completa todos los campos.');
        return;
      }

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        alert('Introduce un email válido.');
        return;
      }

      this.showForm = false;
      this.enviandoCarta = true;

      const payload = {
        ...this.formData,
        carta: this.structured
      };

      const baseUrl =
        import.meta.env.MODE === 'development'
          ? 'http://localhost:8000'
          : window.location.origin;

      try {
        const res = await fetch(`${baseUrl}/api/enviar-carta/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error('Error al enviar la carta.');

        this.structured = [];
        this.formData = { nombre_restaurante: '', email: '' };
        this.$refs.grabador?.reset?.();
        this.enviadoConExito = true;
      } catch (e) {
        console.error(e);
        alert('Hubo un error al enviar la carta.');
      } finally {
        this.enviandoCarta = false;
      }

      setTimeout(() => {
        this.enviadoConExito = false;
      }, 3000);
    }
  }
};
</script>

<style>
body, html {
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}

.logo-container {
  background-color: white;
  text-align: center;
  padding: 1rem 0 0.5rem;
}
.logo {
  width: 300px;
  display: block;
  margin: 0 auto;
}

.app {
  font-family: sans-serif;
  text-align: center;
  padding: 1rem;
  width: 100%;
  max-width: none;
  box-sizing: border-box;
}

.ejemplo-label {
  font-weight: bold;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}

.tabla-wrapper {
  width: 100%;
  padding: 0 0.5rem;
  box-sizing: border-box;
  margin-bottom: 5rem;
}

.menu-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.menu-table th, .menu-table td {
  border: 1px solid #ccc;
  padding: 0.4rem;
  text-align: center;
  vertical-align: middle;
}

.menu-table th:nth-child(1),
.menu-table td:nth-child(1) {
  width: 25%;
}
.menu-table th:nth-child(2),
.menu-table td:nth-child(2) {
  width: 50%;
}
.menu-table th:nth-child(3),
.menu-table td:nth-child(3) {
  width: 10%;
}
.menu-table th:nth-child(4),
.menu-table td:nth-child(4) {
  width: 15%;
}

.menu-table input,
.menu-table textarea {
  width: 100%;
  font-size: 14px;
  padding: 6px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
  resize: none;
  overflow-wrap: break-word;
  white-space: normal;
}

.fixed-buttons {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  background: #ffffff;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  z-index: 10;
  box-sizing: border-box;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal {
  background: white;
  padding: 2rem 1rem;
  border-radius: 12px;
  width: 100%;
  max-width: 95vw;
  text-align: center;
  box-sizing: border-box;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
}

.modal input {
  width: 100%;
  margin: 0.5rem 0;
  padding: 0.5rem;
}

.modal-buttons {
  display: flex;
  justify-content: space-around;
  margin-top: 1rem;
}

.modal-envio {
  background: white;
  padding: 2rem 1.5rem;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  text-align: left;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
  box-sizing: border-box;
}

.modal-envio h3 {
  margin-bottom: 1rem;
  text-align: center;
}

.modal-envio .form-group {
  margin-bottom: 1rem;
}

.modal-envio label {
  display: block;
  margin-bottom: 0.3rem;
  font-weight: bold;
}

.modal-envio input {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 14px;
}

.modal-envio .modal-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 1.5rem;
}

.modal-envio .modal-buttons button {
  flex: 1;
  padding: 0.6rem;
  margin: 0 0.5rem;
  font-size: 14px;
  border-radius: 6px;
  cursor: pointer;
  border: none;
}

.modal-envio .confirm {
  background-color: #007bff;
  color: white;
}

.modal-envio .cancel {
  background-color: #ccc;
  color: #333;
}


@media (max-width: 480px) {
  .tabla-wrapper {
    padding: 0 0.25rem;
  }

  .modal {
    padding: 1.5rem 0.5rem;
  }

  .fixed-buttons {
    flex-direction: row;
    margin-top: 8rem;
  }
}

.button-cross{
  padding: 0 !important;
}

.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ccc;
  z-index: 10;
  max-height: 150px;
  overflow-y: auto;
  list-style: none;
  padding: 0;
  margin: 0;
}

.suggestions li {
  padding: 8px;
  cursor: pointer;
}

.suggestions li:hover {
  background-color: #f0f0f0;
}

.error-message {
  color: #b20000;
  background: #ffe5e5;
  padding: 0.8rem;
  border-radius: 8px;
  margin: 1rem auto;
  max-width: 500px;
  text-align: center;
  font-weight: bold;
}

.menu-table tr.incompleta {
  background-color: #ffe5e5;
}

</style>
