<template>
  <div>
    <nav-bar></nav-bar>
    <div class="container">
      <div class="row mt-4">
        <div class="col-12">
          <h5 class="text-center mb-4">Files and Logs</h5>
          <hr/>
        </div>
      </div>
      <div class="row mt-4" v-if="isAdmin">
        <div class="col-4">
          <form @submit.prevent="getLogs">
            <div class="form-group">
              <label>Select User</label>
              <b-form-select v-model="userId" :options="users"></b-form-select>
            </div>
            <button type="submit" class="btn btn-primary mb-2">Get Logs</button>
          </form>
        </div>
      </div>
      <div class="row mt-4 mb-4">
        <div class="col-8">
          <div class="responsive shadow">
            <b-table
              id="logs-table"
              head-variant="dark"
              borderless
              striped
              hover
              :items="logData"
              :busy="isLoading"
              :fields="fields"
              :per-page="perPage"
              :current-page="currentPage"
            >
              <template v-slot:table-busy>
                <div class="text-center text-danger my-2">
                  <b-spinner class="align-middle"></b-spinner> <strong>Loading...</strong>
                </div>
              </template>
              <template v-slot:cell(action)="data">
                <div class="text-center">
                  <a href="#" class="text-secondary">
                    <i class="fas fa-cloud-download-alt" v-on:click="downloadLogFile(data.item['log file'])"></i>
                  </a>
                </div>
              </template>
            </b-table>
          </div>
          <div class="text-center">
            <b-pagination
              v-model="currentPage"
              :total-rows="rows"
              :per-page="perPage"
              aria-controls="logs-table"
            >
            </b-pagination>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import NavBar from '../components/NavBar.vue';

export default {
  components: {
    NavBar,
  },
  data() {
    return {
      rows: 0,
      perPage: 5,
      currentPage: 1,
      logData: [],
      isLoading: false,
      userId: 0,
      isAdmin: false,
      fields: [
        { key: 'log file', sortable: true },
        { key: 'date', sortable: true },
        { key: 'size', sortable: true },
        'action',
      ],
      users: [],
      users_objects: [],
    };
  },
  created() {
    this.role = this.$store.getters.getUser.role;
    this.isAdmin = this.role === 'admin';
    this.getLogs();
    this.getUsers();
  },
  methods: {
    getLogs() {
      this.isLoading = true;
      axios.get('logs', { params: { 'user-id': this.userId } }).then((response) => {
        this.isLoading = false;
        this.logData = response.data;
        this.rows = this.logData.length;
      }).catch((error) => {
        this.isLoading = false;
        // eslint-disable-next-line no-console
        console.log(error);
      });
    },
    downloadLogFile(name) {
      const getData = { responseType: 'blob', params: { 'user-id': this.userId, file: name } };
      axios.get('logs', getData).then((response) => {
        const fileURL = window.URL.createObjectURL(new Blob([response.data]));
        const fileLink = document.createElement('a');
        fileLink.href = fileURL;
        fileLink.setAttribute('download', `${name}`);
        document.body.appendChild(fileLink);
        fileLink.click();
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
      });
    },
    getUsers() {
      axios.get('user').then((response) => {
        this.users_objects = response.data.users;
        this.users_objects.forEach((item) => {
          this.users.push({ value: item.id, text: item.email });
        });
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
      });
    },
  },
};
</script>
