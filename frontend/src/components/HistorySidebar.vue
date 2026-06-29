<template>
  <div class="history-sidebar" v-if="items.length">
    <h3>История запросов</h3>
    <ul>
      <li v-for="(item, index) in items" :key="index" class="history-item">
        <span @click="selectItem(item)" class="history-text">{{ truncate(item.text) }}</span>
        <button @click.stop="removeItem(index)" class="delete-btn" title="Удалить">✕</button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const STORAGE_KEY = 'biograph-history'
const items = ref([])

onMounted(() => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      items.value = JSON.parse(saved)
    }
  } catch (e) {
    console.warn('Failed to load history from localStorage', e)
  }
})

function saveToStorage() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items.value))
}

function truncate(text, maxWords = 10) {
  const words = text.trim().split(/\s+/)
  if (words.length <= maxWords) return text
  return words.slice(0, maxWords).join(' ') + '…'
}

const emit = defineEmits(['select-history'])

function selectItem(item) {
  emit('select-history', item.text)
}

function removeItem(index) {
  items.value.splice(index, 1)
  saveToStorage()
}

function addItem(text) {
  if (items.value.length && items.value[0].text === text) return
  items.value.unshift({ text })
  if (items.value.length > 20) items.value.pop()
  saveToStorage()
}

defineExpose({ addItem })
</script>

<style scoped>
.history-sidebar {
  width: 260px;
  max-height: 70vh;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  overflow-y: auto;
  font-family: Arial, sans-serif;
}
h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  color: #333;
}
ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.history-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 8px 4px;
  border-bottom: 1px solid #f0f0f0;
}
.history-item:last-child {
  border-bottom: none;
}
.history-text {
  flex: 1;
  font-size: 14px;
  color: #333;
  word-break: break-word;
  margin-right: 8px;
  cursor: pointer;
}
.history-text:hover {
  color: #4a90d9;
}
.delete-btn {
  background: none;
  border: none;
  color: #999;
  font-size: 16px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}
.delete-btn:hover {
  color: #d9534f;
}
</style>