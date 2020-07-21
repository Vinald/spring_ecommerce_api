<template>
  <div class="container">
    <div class="row mt-4">
      <div class="col-md-8">
        <h5 class="text-center mb-4">Apps</h5>
        <div v-if="appsLoading" class="text-center">
          <i class="fas fa-circle-notch fa-spin text-primary"></i> Loading apps...
        </div>
        <div v-else class="table-responsive">
          <b-table striped hover :items="apps" :fields="fields"></b-table>
        </div>
      </div>
      <div class="col-md-4">
        <form>
          <div class="form-group">
            <label for="exampleInputEmail1">Email address</label>
            <input type="email" class="form-control" id="exampleInputEmail1" aria-describedby="emailHelp">
            <small id="emailHelp" class="form-text text-muted">We'll never share your email with anyone else.</small>
          </div>
          <div class="form-group">
            <label for="exampleInputPassword1">Password</label>
            <input type="password" class="form-control" id="exampleInputPassword1">
          </div>
          <div class="form-group form-check">
            <input type="checkbox" class="form-check-input" id="exampleCheck1">
            <label class="form-check-label" for="exampleCheck1">Check me out</label>
          </div>
          <button type="submit" class="btn btn-primary">Submit</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Apps',
  data() {
    return {
      url: process.env.VUE_APP_ROOT_API,
      apps: [],
      form: {},
      creatingApp: false,
      appsLoading: false,
      fields: ['id', 'name', 'date_created'],
    };
  },
  mounted() {
    this.getApps();
  },
  methods: {
    getApps() {
      this.appsLoading = true;
      // eslint-disable-next-line no-unused-vars
      axios.get(`${this.url}/apps`).then((response) => {
        this.apps = response.data.apps;
        this.appsLoading = false;
        // eslint-disable-next-line no-unused-vars
      }).catch((error) => {
        this.appsLoading = false;
        // eslint-disable-next-line no-console
        console.log(this.apps);
      });
    },
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">

</style>
