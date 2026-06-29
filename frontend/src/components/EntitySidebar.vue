<template>
  <div v-if="node" class="sidebar">
    <button class="close-btn" @click="$emit('close')">✕</button>
    <h3>{{ node.data.label }}</h3>
    <p><strong>Тип:</strong> {{ node.data.type }}</p>
    <div v-if="relatedEdges.length">
      <strong>Связанные факты:</strong>
      <ul>
        <li v-for="(edge, idx) in relatedEdges" :key="idx">
          {{ formatEdge(edge) }}
        </li>
      </ul>
    </div>
    <button @click="$emit('recommend', node.data.id)" :disabled="loading">
      {{ loading ? 'Загрузка...' : 'Найти похожих людей' }}
    </button>
    <div v-if="recommendations.length" class="recommendations">
      <strong>Похожие люди:</strong>
      <ul>
        <li v-for="rec in recommendations" :key="rec.id">{{ rec.name }} (общих связей: {{ rec.weight }})</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  node: Object,
  edges: Array,
  nodes: Array
})
const emit = defineEmits(['recommend', 'close'])

const loading = ref(false)
const recommendations = ref([])

const nodeMap = computed(() => {
  const map = {}
  if (props.nodes) {
    props.nodes.forEach(n => {
      map[n.data.id] = n.data.label
    })
  }
  return map
})

const relatedEdges = computed(() => {
  if (!props.node) return []
  return props.edges.filter(
    e => e.data.source === props.node.data.id || e.data.target === props.node.data.id
  )
})

function formatEdge(edge) {
  const label = edge.data.label || 'связан'
  const sourceName = nodeMap.value[edge.data.source] || edge.data.source
  const targetName = nodeMap.value[edge.data.target] || edge.data.target
  if (edge.data.source === props.node.data.id) {
    return `${label} → ${targetName}`
  } else {
    return `${label} ← ${sourceName}`
  }
}

function setLoading(val) { loading.value = val }
function setRecommendations(recs) { recommendations.value = recs }
function clearRecommendations() { recommendations.value = [] }

defineExpose({ setLoading, setRecommendations, clearRecommendations })
</script>

<style scoped>
.sidebar {
  width: 280px;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  font-family: Arial, sans-serif;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;  /* для кнопки закрытия */
}
.close-btn {
  position: absolute;
  top: 8px;
  right: 12px;
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #999;
  width: auto;
  padding: 0;
  margin: 0;
}
.close-btn:hover {
  color: #333;
}
button {
  margin-top: 12px;
  width: 100%;
  padding: 8px;
  background: #4a90d9;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
button:disabled { background: #a0c4e8; }
.recommendations { margin-top: 12px; }
</style>