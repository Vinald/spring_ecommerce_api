<template>
  <div>
    <div v-if="isChartLoading" class="text-center">
      <b-spinner class="align-middle"></b-spinner> <strong>Loading...</strong>
    </div>
    <line-chart v-if="chartType==='line'" :download="{background: '#fff'}" :data="chartData"></line-chart>
    <column-chart v-if="chartType==='column'" :download="{background: '#fff'}" :data="chartData"></column-chart>
  </div>
</template>

<script>
export default {
  name: 'Chart',
  props: ['isChartLoading', 'chartType', 'chartData'],
};
</script>
