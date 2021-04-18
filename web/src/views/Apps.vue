<template>
  <div>
    <nav-bar></nav-bar>
    <div class="container">
      <div class="row mt-4">
        <div class="col-md-8">
          <div class="text-center" v-if="message">
            <b-alert show dismissible :variant="label">{{ message }}</b-alert>
          </div>
          <h5 class="text-center mb-4" style="font-size: x-large;">Apps</h5>
          <div class="table-responsive shadow">
            <b-table
              outlined
              head-variant="dark"
              striped
              borderless
              hover
              :items="apps"
              :fields="fields"
              :busy="appsLoading"
            >
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
                  <div class="table-responsive shadow">
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
                        <tr>
                          <th scope="row">Toll-free</th>
                          <td><code>{{ data.item.toll_free }}</code></td>
                        </tr>
                        <tr>
                          <th scope="row">Caller ID</th>
                          <td><code>{{ data.item.caller_id }}</code></td>
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
                    <div class="form-group" v-if="isAdmin">
                      <label for="app-edit-telephone">Application Telephone</label>
                      <input type="text" class="form-control" id="app-edit-telephone" v-model="editForm.phone">
                    </div>
                    <div class="form-group" v-if="isAdmin">
                      <label for="app-edit-toll-free">Application Toll-free</label>
                      <input type="text" class="form-control" id="app-edit-toll-free" v-model="editForm.toll_free">
                    </div>
                    <div class="form-group" v-if="isAdmin">
                      <label for="app-edit-caller-id">Application Caller ID</label>
                      <input type="text" class="form-control" id="app-edit-caller-id" v-model="editForm.caller_id">
                    </div>
                    <button type="submit" class="btn btn-primary float-right">Save</button>
                  </form>
                </b-modal>
              </template>
            </b-table>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card shadow">
            <div class="card-header bg-dark text-white text-center" style="font-size: large;">
              Create a new application
            </div>
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
                <div class="form-group" v-if="isAdmin">
                  <label for="app-caller-id">Application Caller ID</label>
                  <input
                    type="text"
                    class="form-control"
                    id="app-caller-id"
                    v-model="createAppForm.caller_id"
                    placeholder="e.g +25632XX"
                  >
                </div>
                <div class="form-group" v-if="isAdmin">
                  <label for="app-toll-free">Application Toll-free</label>
                  <input
                    type="text"
                    class="form-control"
                    id="app-toll-free"
                    v-model="createAppForm.toll_free"
                    placeholder="e.g 0800XXX"
                  >
                </div>
                <div class="form-group" v-if="isAdmin">
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
                <button v-else type="submit" class="btn btn-primary float-right shadow">Save</button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import qs from 'qs';
import NavBar from '../components/NavBar.vue';

export default {
  name: 'Apps',
  components: {
    NavBar,
  },
  data() {
    return {
      url: process.env.VUE_APP_ROOT_API,
      apps: [],
      createAppForm: {
        name: '',
        phone: '',
        voice_url: '',
        status_url: '',
        caller_id: '',
        toll_free: '',
      },
      editForm: {
        id: '',
        name: '',
        phone: '',
        voice_url: '',
        status_url: '',
        caller_id: '',
        toll_free: '',
      },
      label: null,
      message: null,
      appName: null,
      creatingApp: false,
      appsLoading: false,
      fields: [
        { key: 'id', label: '#', sortable: true },
        'name',
        { key: 'caller_id', label: 'Caller ID' },
        'toll_free',
        'phone',
        'owner',
        'action',
      ],
      isAdmin: false,
      role: '',
    };
  },
  created() {
    this.role = this.$store.getters.getUser.role;
    this.isAdmin = this.role === 'admin';
    this.getApps();
  },
  methods: {
    createNewApp() {
      this.creatingApp = true;
      axios.post('apps', qs.stringify(this.createAppForm)).then((response) => {
        const { status } = response.data;
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
        this.creatingApp = false;
        this.initCreateForm();
        this.getApps();
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.creatingApp = false;
      });
    },
    getApps() {
      this.appsLoading = true;
      axios.get('apps').then((response) => {
        this.apps = response.data.apps;
        this.appsLoading = false;
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.appsLoading = false;
      });
    },
    deleteApp(id) {
      this.appsLoading = true;
      axios.delete('apps', { params: { id } }).then((response) => {
        const { status } = response.data;
        this.getApps();
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.appsLoading = false;
      });
    },
    updateApp() {
      this.$bvModal.hide(`${this.editForm.id}apps-edit-modal`);
      this.appsLoading = true;
      axios.put('apps', qs.stringify(this.editForm)).then((response) => {
        const { status } = response.data;
        this.getApps();
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
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
