<template>
  <div id="app">
    <h1>BioGraph Nexus</h1>
    <TextInput ref="textInput" @submit="handleSubmit" />
    <div v-if="error" class="error">{{ error }}</div>
    <div class="main-layout" v-if="graphData">
      <GraphView
        :graphData="graphData"
        @node-click="onNodeClick"
        ref="graphView"
      />
    <EntitySidebar
      v-if="selectedNode"
      :node="selectedNode"
      :edges="graphData.edges"
      :nodes="graphData.nodes"
      @recommend="onRecommend"
      ref="sidebar"
    />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import TextInput from './components/TextInput.vue'
import GraphView from './components/GraphView.vue'
import EntitySidebar from './components/EntitySidebar.vue'

const textInput = ref(null)
const graphView = ref(null)
const sidebar = ref(null)
const error = ref('')
const graphData = ref(null)
const selectedNode = ref(null)

async function handleSubmit(text) {
  error.value = ''
  graphData.value = null
  selectedNode.value = null
  try {
    const response = await axios.post('http://localhost:8000/extract', { text })
    const { entities, relations } = response.data
    const nodes = entities.map(e => ({
      data: { id: e.entity_id, label: e.name, type: e.type }
    }))
    const edges = relations.map(r => ({
      data: {
        source: r.subject.entity_id,
        target: r.object.entity_id,
        label: r.relation
      }
    }))
    graphData.value = { nodes, edges }
  } catch (err) {
    console.error(err)
    error.value = err.response?.data?.detail || 'Неизвестная ошибка при обработке'
  } finally {
    if (textInput.value) textInput.value.setLoading(false)
  }
}

function onNodeClick(nodeData) {
  selectedNode.value = { data: nodeData }   // оборачиваем, чтобы EntitySidebar видел node.data
}

async function onRecommend(entityId) {
  if (!sidebar.value) return
  sidebar.value.setLoading(true)
  try {
    // Временная заглушка — позже заменим на реальный запрос
    const response = await axios.get(`http://localhost:8000/recommend?entity_id=${entityId}`)
    sidebar.value.setRecommendations(response.data.recommendations)
  } catch (err) {
    console.error(err)
  } finally {
    sidebar.value.setLoading(false)
  }
}
</script>

<style>
body { margin: 0; font-family: Arial, sans-serif; }
#app { padding: 20px; }
.error {
  color: #d9534f;
  margin-top: 12px;
  padding: 10px;
  background-color: #f9e8e8;
  border-radius: 8px;
}
.main-layout {
  display: flex;
  gap: 20px;
}
</style>