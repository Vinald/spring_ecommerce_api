<template>
  <div>
    <nav-bar></nav-bar>
    <div class="container">
      <div class="row mt-4">
        <div class="col-md-8">
          <div class="text-center" v-if="message">
            <b-alert show dismissible :variant="label">{{ message }}</b-alert>
          </div>
          <h5 class="text-center mb-4" style="font-size: x-large;">Users</h5>
          <div class="table-responsive shadow">
            <b-table
              outlined
              head-variant="dark"
              striped
              borderless
              hover
              :items="users"
              :fields="fields"
              :busy="usersLoading"
              class="text-center"
            >
              <template v-slot:table-busy>
                <div class="text-center text-danger my-2">
                  <b-spinner class="align-middle"></b-spinner> <strong>Loading...</strong>
                </div>
              </template>
              <template v-slot:cell(role)="data">
                <i v-if="data.item.role === 'admin'" class="fas fa-check-circle text-success"></i>
              </template>
              <template v-slot:cell(action)="data">
                <b-button-group>
                  <b-button @click="editUser(data.item)" variant="info"><i class="fas fa-edit"></i></b-button>
                  <b-button @click="deleteUser(data.item.id)" variant="danger"><i class="fas fa-trash"></i></b-button>
                </b-button-group>
                <b-modal :id="data.item.id + 'users-edit-modal'" :title="'Update user: ' + data.item.email" hide-footer>
                  <form @submit.prevent="updateUser()">
                    <div class="form-group">
                      <label>Role</label>
                      <b-form-select v-model="editForm.role" :options="roles"></b-form-select>
                    </div>
                    <div class="form-group">
                      <label for="user-edit-email">Email</label>
                      <input type="email" class="form-control" id="user-edit-email" v-model="editForm.email">
                    </div>
                    <div class="form-group">
                      <label for="user-edit-password">Password</label>
                      <input type="text" class="form-control" id="user-edit-password" v-model="editForm.password">
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
              Create user
            </div>
            <div class="card-body">
              <form @submit.prevent="createNewUser">
                <div class="form-group">
                  <label>Role</label>
                  <b-form-select v-model="createUserForm.role" :options="roles"></b-form-select>
                </div>
                <div class="form-group">
                  <label for="user-email">Email</label>
                  <input type="email" class="form-control" id="user-email" v-model="createUserForm.email">
                </div>
                <div class="form-group">
                  <label for="user-password">Password</label>
                  <input type="text" class="form-control" id="user-password" v-model="createUserForm.password">
                </div>
                <b-button v-if="creatingUser" variant="primary" class="float-right">
                  <i class="fas fa-circle-notch fa-spin text-primary"></i> Creating new user...
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
      users: [],
      roles: [],
      createUserForm: {
        role: '',
        email: '',
        password: Math.random().toString(36).slice(-10),
      },
      editForm: {
        id: '',
        role: '',
        email: '',
        password: '',
      },
      label: null,
      message: null,
      appName: null,
      creatingUser: false,
      usersLoading: false,
      fields: [
        { key: 'id', label: '#', sortable: true },
        'email',
        { key: 'role', label: 'Admin' },
        { key: 'creation_date', label: 'Date Registered' },
        'action',
      ],
    };
  },
  created() {
    this.getRoles();
    this.getUsers();
  },
  methods: {
    createNewUser() {
      this.creatingUser = true;
      axios.post('user', qs.stringify(this.createUserForm)).then((response) => {
        const { status } = response.data;
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
        this.creatingUser = false;
        this.initCreateForm();
        this.getUsers();
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.creatingUser = false;
      });
    },
    getUsers() {
      this.usersLoading = true;
      axios.get('user').then((response) => {
        this.users = response.data.users;
        this.usersLoading = false;
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.usersLoading = false;
      });
    },
    deleteUser(id) {
      this.usersLoading = true;
      axios.delete('user', { params: { id } }).then((response) => {
        const { status } = response.data;
        this.getUsers();
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.usersLoading = false;
      });
    },
    updateUser() {
      this.$bvModal.hide(`${this.editForm.id}users-edit-modal`);
      this.usersLoading = true;
      axios.put('user', qs.stringify(this.editForm)).then((response) => {
        const { status } = response.data;
        this.getUsers();
        this.label = status === 'success' ? 'success' : 'danger';
        this.message = response.data.message;
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
        this.usersLoading = false;
      });
    },
    editUser(data) {
      this.editForm = data;
      this.$bvModal.show(`${this.editForm.id}users-edit-modal`);
    },
    initCreateForm() {
      this.createUserForm.role = '';
      this.createUserForm.email = '';
      this.createUserForm.password = '';
    },
    getRoles() {
      axios.get('roles').then((response) => {
        this.roles = response.data;
      }).catch((error) => {
        // eslint-disable-next-line no-console
        console.log(error);
      });
    },
  },
};
</script>
