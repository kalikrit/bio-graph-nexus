<template>
  <div class="text-input">
    <textarea
      v-model="text"
      placeholder="Вставьте текст биографии..."
      rows="8"
      :disabled="loading"
      @input="activeExample = null"
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
          :class="{ active: ex.label === activeExample }"
          @click="loadExample(ex)"
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
const activeExample = ref(null)

const examples = [
  {
    label: 'Стив Джобс',
    text: 'Steve Jobs founded Apple Inc. in Cupertino on April 1, 1976. He later worked at Pixar and NeXT Computer.'
  },
  {
    label: 'Мария Кюри',
    text: 'Marie Curie was born in Warsaw. She studied at the Sorbonne and discovered radium with Pierre Curie.'
  },
  {
    label: 'George Boole',
    text: `George Boole was born in Lincoln on 2 November 1815.
George Boole established his own school at the age of 19.
George Boole served as the first professor of mathematics at Queen's College in Cork.
George Boole met Mary Everest at Queen's College.
George Boole developed Boolean algebra in 1847.
George Boole wrote the book 'The Laws of Thought' in 1854.
George Boole wrote 'Treatise on Differential Equations'.
George Boole wrote 'The Mathematical Analysis of Logic'.
George Boole collaborated with Charles Sanders Peirce.
George Boole collaborated with William Stanley Jevons.
Claude Shannon applied Boolean algebra to electrical relay systems.
Victor Shestakov applied Boolean algebra to digital circuits.
George Boole received the Royal Society's gold prize for mathematics.
George Boole won the Keith Medal.
George Boole won honorary degrees from the Universities of Dublin and Oxford.
George Boole died of pneumonia on 8 December 1864.`
  },
  {
    label: 'Четыре товарища',
    text: `John befriend of Mark.
Steve befriend of John.
Elton befriended of Steve.
John got married to Martha in 1996.
Mark married Lucy.
Mark divorced Lucy. Lucy passed away in 1996.
Mark married Erika.
Erika befriended Martha.
Steve befriended Erika.
Elton married to Sarah.
Elton and Sarah had a son named Mike in 1996.`
  }
]

const emit = defineEmits(['submit', 'clear'])

function handleSubmit() {
  if (!text.value.trim() || loading.value) return
  loading.value = true
  // больше не сбрасываем activeExample, чтобы выделение сохранялось
  emit('submit', text.value)
}

function loadExample(ex) {
  text.value = ex.text
  activeExample.value = ex.label
  emit('clear')
}

function setLoading(value) {
  loading.value = value
}

defineExpose({ setLoading, text })
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
.examples button.active {
  background-color: #357abd;
  color: white;
  border: 2px solid #1e5a8a;
}
</style>