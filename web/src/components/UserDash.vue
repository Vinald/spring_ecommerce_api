<template>
  <div>
    <nav-bar></nav-bar>
    <div class="container">
      <div class="row mt-4 mb-4">
        <div class="col-12">
          <div class="responsive">
            <hr>
            <line-chart :download="{background: '#fff'}" :data="chartData"></line-chart>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import NavBar from './NavBar.vue';

export default {
  components: {
    NavBar,
  },
  data() {
    return {
      chartData: [],
    };
  },
  created() {
    this.fetchChartData();
  },
  methods: {
    fetchChartData() {
      axios.get('charts').then((response) => {
        this.chartData = response.data;
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
      });
    },
  },
};
</script>
