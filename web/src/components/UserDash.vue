<template>
  <div>
    <nav-bar></nav-bar>
    <div class="container">
      <div class="row mt-4 mb-4">
        <div class="col-12">
          <div class="responsive shadow">
            <div v-if="isChartLoading" class="text-center">
              <b-spinner class="align-middle"></b-spinner> <strong>Loading...</strong>
            </div>
            <line-chart v-else :download="{background: '#fff'}" :data="chartData"></line-chart>
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
