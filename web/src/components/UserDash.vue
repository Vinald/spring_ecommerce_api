<template>
  <div>
    <nav-bar></nav-bar>
    <div class="container">
      <div class="row mt-4 mb-4">
        <div class="col-12">
          <div class="responsive shadow">
            <b-button-group>
              <b-button v-on:click="chartType = 'column'">Column</b-button>
              <b-button v-on:click="chartType = 'line'">Line</b-button>
            </b-button-group>
            <chart :chart-type="chartType" :is-chart-loading="isChartLoading" :chart-data="chartData"></chart>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import NavBar from './NavBar.vue';
import Chart from './Chart.vue';

export default {
  components: {
    Chart,
    NavBar,
  },
  data() {
    return {
      chartType: 'column',
      chartData: [],
      isChartLoading: false,
    };
  },
  created() {
    this.fetchChartData();
  },
  methods: {
    fetchChartData() {
      this.isChartLoading = true;
      axios.get('charts').then((response) => {
        this.isChartLoading = false;
        this.chartData = response.data;
      }).catch((error) => {
        this.isChartLoading = false;
        // eslint-disable-next-line no-console
        console.log(error);
      });
    },
  },
};
</script>
