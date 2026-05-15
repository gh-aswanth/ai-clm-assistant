<template>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    <div v-for="template in templates" :key="template.id" class="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 hover:shadow-md transition">
      <div class="flex justify-between items-start mb-4">
        <h3 class="font-bold text-gray-900 dark:text-white">{{ template.name }}</h3>
        <span class="px-2 py-1 text-[10px] font-bold uppercase rounded bg-blue-100 text-blue-700">{{ template.category }}</span>
      </div>
      <p class="text-sm text-gray-500 mb-4 line-clamp-3">{{ template.content }}</p>
      <div class="flex justify-between items-center text-xs text-gray-400">
        <span>Version {{ template.version }}</span>
        <button class="text-blue-600 font-bold hover:underline">Use Template</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const templates = ref([
  { id: 1, name: 'Standard Roads Agreement', category: 'Ministry', content: 'Standard terms and conditions for highway construction and maintenance projects...', version: 1 },
  { id: 2, name: 'General Service Contract', category: 'General', content: 'General conditions for supply of services to government departments...', version: 2 },
])

onMounted(async () => {
  try {
    const response = await axios.get('/api/templates/')
    if (response.data && response.data.length > 0) {
      templates.value = response.data
    }
  } catch (error) {
    console.error('Failed to fetch templates:', error)
  }
})
</script>
