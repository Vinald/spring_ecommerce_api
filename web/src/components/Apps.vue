<template>
  <div class="container">
    <div class="row mt-4">
      <div class="col-md-8">
        <div class="text-center" v-if="message">
          <b-alert show dismissible :variant="label">{{ message }}</b-alert>
        </div>
        <h5 class="text-center mb-4">Apps</h5>
        <div class="table-responsive">
          <b-table outlined hover :items="apps" :fields="fields" :busy="appsLoading">
            <template v-slot:table-busy>
              <div class="text-center text-danger my-2">
                <b-spinner class="align-middle"></b-spinner> <strong>Loading...</strong>
              </div>
            </template>
            <template v-slot:cell(action)="data">
              <b-button-group>
                <b-button @click="$bvModal.show(data.item.id + 'apps-view-modal')" variant="primary">
                  <i class="fas fa-eye"></i>
                </b-button>
                <b-button @click="editApp(data.item)" variant="info"><i class="fas fa-edit"></i></b-button>
                <b-button @click="deleteApp(data.item.id)" variant="danger"><i class="fas fa-trash"></i></b-button>
              </b-button-group>
              <b-modal :id="data.item.id + 'apps-view-modal'" size="lg" hide-footer>
                <template v-slot:modal-title>
                  {{ data.item.name }}
                </template>
                <div class="table-responsive">
                  <table class="table table-sm table-bordered table-striped">
                    <tbody>
                      <tr>
                        <th scope="row">Name</th>
                        <td>{{ data.item.name }}</td>
                      </tr>
                      <tr>
                        <th scope="row">Telephone</th>
                        <td><code>{{ data.item.phone }}</code></td>
                      </tr>
                      <tr>
                        <th scope="row">Token</th>
                        <td><code>{{ data.item.token }}</code></td>
                      </tr>
                      <tr>
                        <th scope="row">Voice URL</th>
                        <td><code>{{ data.item.voice_url }}</code></td>
                      </tr>
                      <tr>
                        <th scope="row">Status URL</th>
                        <td><code>{{ data.item.status_url }}</code></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <b-button
                  class="mt-3 float-right"
                  variant="info"
                  @click="$bvModal.hide(data.item.id + 'apps-view-modal')"
                >
                  Close
                </b-button>
              </b-modal>
              <b-modal :id="data.item.id + 'apps-edit-modal'" :title="'Update app: ' + data.item.name" hide-footer>
                <form @submit.prevent="updateApp()">
                  <div class="form-group">
                    <label for="app-edit-name">Application name</label>
                    <input type="text" class="form-control" id="app-edit-name" v-model="editForm.name">
                  </div>
                  <div class="form-group">
                    <label for="app-edit-voice-url">Application Voice URL</label>
                    <input type="text" class="form-control" id="app-edit-voice-url" v-model="editForm.voice_url">
                  </div>
                  <div class="form-group">
                    <label for="app-edit-status-url">Application Status URL</label>
                    <input type="text" class="form-control" id="app-edit-status-url" v-model="editForm.status_url">
                  </div>
                  <div class="form-group">
                    <label for="app-edit-telephone">Application Telephone</label>
                    <input type="text" class="form-control" id="app-edit-telephone" v-model="editForm.phone">
                  </div>
                  <button type="submit" class="btn btn-primary float-right">Save</button>
                </form>
              </b-modal>
            </template>
          </b-table>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card">
          <div class="card-header text-center">Create a new application</div>
          <div class="card-body">
            <form @submit.prevent="createNewApp">
              <div class="form-group">
                <label for="app-name">Application name</label>
                <input type="text" class="form-control" id="app-name" v-model="createAppForm.name">
              </div>
              <div class="form-group">
                <label for="app-voice-url">Application Voice URL</label>
                <input type="text" class="form-control" id="app-voice-url" v-model="createAppForm.voice_url">
              </div>
              <div class="form-group">
                <label for="app-status-url">Application Status URL</label>
                <input type="text" class="form-control" id="app-status-url" v-model="createAppForm.status_url">
              </div>
              <div class="form-group">
                <label for="app-phone">Application Telephone</label>
                <input
                  type="text"
                  id="app-phone"
                  class="form-control"
                  v-model="createAppForm.phone"
                  placeholder="e.g 25678XX"
                >
              </div>
              <b-button v-if="creatingApp" variant="primary" class="float-right">
                <i class="fas fa-circle-notch fa-spin text-primary"></i> Creating new app...
              </b-button>
              <button v-else type="submit" class="btn btn-primary float-right">Save</button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import qs from 'qs';

export default {
  name: 'Apps',
  data() {
    return {
      url: process.env.VUE_APP_ROOT_API,
      apps: [],
      createAppForm: {
        name: '',
        phone: '',
        voice_url: '',
        status_url: '',
      },
      editForm: {
        id: '',
        name: '',
        phone: '',
        voice_url: '',
        status_url: '',
      },
      label: null,
      message: null,
      appName: null,
      creatingApp: false,
      appsLoading: false,
      fields: ['id', 'name', 'date_created', 'phone', 'action'],
    };
  },
  mounted() {
    this.getApps();
  },
  methods: {
    createNewApp() {
      this.creatingApp = true;
      axios.post(`${this.url}/apps`, qs.stringify(this.createAppForm)).then((response) => {
        const { status } = response.data;
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
        this.creatingApp = false;
        this.initCreateForm();
        this.getApps();
        // eslint-disable-next-line no-unused-vars
      }).catch((error) => {
        this.creatingApp = false;
      });
    },
    getApps() {
      this.appsLoading = true;
      axios.get(`${this.url}/apps`).then((response) => {
        this.apps = response.data.apps;
        this.appsLoading = false;
        // eslint-disable-next-line no-unused-vars
      }).catch((error) => {
        this.appsLoading = false;
      });
    },
    deleteApp(id) {
      this.appsLoading = true;
      axios.delete(`${this.url}/apps`, { params: { id } }).then((response) => {
        const { status } = response.data;
        this.getApps();
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
        // eslint-disable-next-line no-unused-vars
      }).catch((error) => {
        this.appsLoading = false;
      });
    },
    updateApp() {
      this.$bvModal.hide(`${this.editForm.id}apps-edit-modal`);
      this.appsLoading = true;
      axios.put(`${this.url}/apps`, qs.stringify(this.editForm)).then((response) => {
        const { status } = response.data;
        this.getApps();
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
        // eslint-disable-next-line no-unused-vars
      }).catch((error) => {
        this.appsLoading = false;
      });
    },
    editApp(data) {
      this.editForm = data;
      this.$bvModal.show(`${this.editForm.id}apps-edit-modal`);
    },
    initCreateForm() {
      this.createAppForm.name = '';
      this.createAppForm.phone = '';
      this.createAppForm.voice_url = '';
      this.createAppForm.status_url = '';
    },
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">

</style>
