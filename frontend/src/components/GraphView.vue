<template>
  <div class="graph-container" ref="graphContainer"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import cytoscape from 'cytoscape'
import coseBilkent from 'cytoscape-cose-bilkent'

cytoscape.use(coseBilkent)

const emit = defineEmits(['nodeClick'])

const props = defineProps({
  graphData: {
    type: Object,
    default: () => ({ nodes: [], edges: [] })
  }
})

const graphContainer = ref(null)
let cy = null

function renderGraph() {
  if (!graphContainer.value) return
  if (cy) {
    cy.destroy()
  }

  const elements = [
    ...props.graphData.nodes.map(n => ({ data: n.data })),
    ...props.graphData.edges.map(e => ({ data: e.data }))
  ]

  cy = cytoscape({
    container: graphContainer.value,
    elements,
    style: [
    {
        selector: 'node',
        style: {
        'label': 'data(label)',
        'font-size': '14px',
        'text-valign': 'center',
        'text-halign': 'center',
        'text-outline-color': '#1e1e1e',
        'text-outline-width': 3,
        'border-width': 2,
        'border-color': '#fff',
        }
    },
    {
        selector: 'node[type="PERSON"]',
        style: {
        'background-color': '#4287f5',
        'shape': 'ellipse',
        'color': '#ffffff',
        'text-outline-color': '#4287f5',
        }
    },
    {
        selector: 'node[type="ORG"]',
        style: {
        'background-color': '#42f554',
        'shape': 'rectangle',
        'color': '#1e1e1e',
        'text-outline-color': '#42f554',
        }
    },
    {
        selector: 'node[type="GPE"]',
        style: {
        'background-color': '#f5a742',
        'shape': 'diamond',
        'color': '#1e1e1e',
        'text-outline-color': '#f5a742',
        }
    },
    {
        selector: 'node[type="DATE"]',
        style: {
        'background-color': '#cccccc',
        'shape': 'hexagon',
        'color': '#1e1e1e',
        'text-outline-color': '#cccccc',
        }
    },
    {
        selector: 'edge',
        style: {
        'width': 2,
        'line-color': '#888',
        'target-arrow-color': '#888',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'label': 'data(label)',
        'color': '#ccc',
        'font-size': '11px',
        'text-rotation': 'autorotate',
        'text-outline-color': '#1e1e1e',
        'text-outline-width': 2,
        }
    }
    ],
    layout: {
      name: 'cose-bilkent',
      animate: true,
      animationDuration: 1000,
    },
    userZoomingEnabled: true,
    userPanningEnabled: true,
    zoomingEnabled: true,
    panningEnabled: true,
  })

    cy.on('tap', 'node', (evt) => {
    const node = evt.target
    emit('nodeClick', node.data())
    })
}

onMounted(() => {
  renderGraph()
})

onBeforeUnmount(() => {
  if (cy) cy.destroy()
})

watch(() => props.graphData, () => {
  renderGraph()
}, { deep: true })
</script>

<style scoped>
.graph-container {
  width: 100%;
  height: 600px;
  border: 1px solid #333;
  border-radius: 8px;
  overflow: hidden;
  margin-top: 20px;
  background-color: darkgray;
}
</style>