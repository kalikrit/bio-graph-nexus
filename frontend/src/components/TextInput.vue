<template>
  <div class="text-input">
    <textarea
      v-model="text"
      placeholder="Вставьте текст биографии..."
      rows="8"
      :disabled="loading"
    ></textarea>
    <div class="controls">
      <button @click="handleSubmit" :disabled="loading || !text.trim()">
        {{ loading ? 'Обрабатываю...' : 'Обработать' }}
      </button>
      <div class="examples">
        <span>Примеры:</span>
        <button
          v-for="ex in examples"
          :key="ex.label"
          @click="loadExample(ex.text)"
          :disabled="loading"
        >
          {{ ex.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const text = ref('')
const loading = ref(false)

const examples = [
  {
    label: 'Стив Джобс',
    text: 'Steve Jobs founded Apple Inc. in Cupertino on April 1, 1976. He later worked at Pixar and NeXT.'
  },
  {
    label: 'Мария Кюри',
    text: 'Marie Curie was born in Warsaw. She studied at the Sorbonne and discovered radium with Pierre Curie.'
  },
  {
    label: 'Четыре товарища',
    text: `John befriend of Mark.
Steve befriend of John.
Elton befriend of Steve.
John was married to Martha.
Mark married Lucy.
Mark divorced Lucy.
Mark married Erika.
Erika befriended Martha.
Steve befriended Erika.
Elton married to Sarah.`
  }
]

const emit = defineEmits(['submit','clear'])

function handleSubmit() {
  if (!text.value.trim() || loading.value) return
  loading.value = true
  emit('submit', text.value)
}

function loadExample(exampleText) {
  text.value = exampleText
  emit('clear')
}

// метод для сброса состояния загрузки снаружи
function setLoading(value) {
  loading.value = value
}

defineExpose({ setLoading })
</script>

<style scoped>
.text-input {
  margin-bottom: 20px;
}
textarea {
  width: 100%;
  padding: 12px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 8px;
  resize: vertical;
  box-sizing: border-box;
}
.controls {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 12px;
  flex-wrap: wrap;
}
button {
  padding: 10px 24px;
  font-size: 16px;
  border: none;
  border-radius: 8px;
  background-color: #4a90d9;
  color: white;
  cursor: pointer;
  transition: background-color 0.2s;
}
button:hover:not(:disabled) {
  background-color: #357abd;
}
button:disabled {
  background-color: #a0c4e8;
  cursor: not-allowed;
}
.examples {
  display: flex;
  align-items: center;
  gap: 8px;
}
.examples span {
  font-size: 14px;
  color: #666;
}
.examples button {
  padding: 6px 12px;
  font-size: 14px;
  background-color: #e9ecef;
  color: #333;
}
.examples button:hover:not(:disabled) {
  background-color: #d3d9df;
}
</style>