<template>
  <div>
    <nav-bar></nav-bar>
    <div class="container">
      <div class="row mt-5">
        <div class="col-md-4"></div>
        <div class="col-md-4">
          <div class="card shadow">
            <div class="card-body">
              <div class="card-title text-center mb-4" style="font-size: 1.5rem">Change Password</div>
              <hr>
              <b-alert v-if="message" show :variant="label" class="text-center">{{ message }}</b-alert>
              <form @submit.prevent="updatePasswordHandler">
                <div class="mb-3">
                  <label for="old-password" class="form-label">Old Password</label>
                  <input type="password" class="form-control" id="old-password" v-model="details.oldPassword">
                </div>
                <div class="mb-3">
                  <label for="new-password" class="form-label">New Password</label>
                  <input type="password" class="form-control" id="new-password" v-model="details.password">
                </div>
                <div class="mb-3">
                  <label for="password" class="form-label">Confirm Password</label>
                  <input type="password" class="form-control" id="password" v-model="details.confirmPassword">
                </div>
                <button type="submit" class="btn btn-danger btn-block">
                  <i v-if="isLoading" class="fas fa-circle-notch fa-spin"></i> Update password
                </button>
              </form>
            </div>
          </div>
        </div>
        <div class="col-md-4"></div>
      </div>
    </div>
  </div>
</template>

<script>
import qs from 'qs';
import axios from 'axios';
import NavBar from '../components/NavBar.vue';

export default {
  name: 'Profile',
  components: {
    NavBar,
  },
  data() {
    return {
      message: null,
      isLoading: false,
      label: null,
      details: {
        oldPassword: '',
        password: '',
        confirmPassword: '',
        action: 'update-password',
      },
    };
  },
  methods: {
    updatePasswordHandler() {
      const isFormValid = this.validateForm();
      if (isFormValid) {
        this.isLoading = true;
        axios.post('profile', qs.stringify(this.details))
          .then((response) => {
            const { status } = response.data;
            this.isLoading = false;
            this.label = status === 'success' ? 'success' : 'danger';
            this.message = response.data.message;
          })
          .catch((error) => {
            // eslint-disable-next-line no-console
            console.log(error);
            this.isLoading = false;
          });
      }
    },
    validateForm() {
      if (this.details.password.match(/^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[a-zA-Z]).{8,}$/) === null) {
        this.label = 'danger';
        this.message = 'Password must be a minimum of 8 characters. Must contain a digit, upper and lower case letter';
        return false;
      }
      if (this.details.password !== this.details.confirmPassword) {
        this.label = 'danger';
        this.message = 'Passwords do not match';
        return false;
      }
      return true;
    },
  },
};

</script>
