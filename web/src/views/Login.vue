<template>
  <div class="container">
    <div class="row mt-5">
      <div class="col-md-4"></div>
      <div class="col-md-4">
        <div class="text-center">
          <b-img fluid :src="logo" alt="logo"></b-img>
        </div>
        <div class="p-4" style="border: #dee2e6 3px solid; border-radius: 4px 4px 4px 4px;">
          <b-alert v-if="message" show variant="danger" class="text-center">{{ message }}</b-alert>
          <form @submit.prevent="loginHandler">
            <h2 class="mt-5 mb-5 text-center" style="font-weight: 300">Academy IVR Login</h2>
            <div class="mb-3">
              <label for="email" class="form-label">Email address</label>
              <input type="email" class="form-control" id="email" v-model="loginDetails.username">
            </div>
            <div class="mb-3">
              <label for="password" class="form-label">Password</label>
              <input type="password" class="form-control" id="password" v-model="loginDetails.password">
            </div>
            <button type="submit" class="btn btn-danger btn-block">
              <i v-if="isLoading" class="fas fa-circle-notch fa-spin"></i> Login
            </button>
          </form>
        </div>
      </div>
      <div class="col-md-4"></div>
    </div>
  </div>
</template>

<script>
import qs from 'qs';
import axios from 'axios';
import academyLogo from '../assets/img/academy.jpg';

export default {
  name: 'Login',
  data() {
    return {
      message: null,
      isLoading: false,
      loginDetails: {
        username: '',
        password: '',
      },
      logo: academyLogo,
    };
  },
  created() {
    if (this.$store.getters.isLoggedIn) {
      this.$router.push('/home');
    } else {
      this.$forceUpdate();
    }
  },
  methods: {
    async loginHandler() {
      let user;
      let token;
      try {
        this.isLoading = true;
        const response = await axios.post('login', qs.stringify(this.loginDetails));
        this.isLoading = false;
        user = response.data.user;
        token = response.data.token;
        this.$store.dispatch('login', { token, user });
        this.$router.push('/home');
      } catch (e) {
        this.isLoading = false;
        this.loginDetails.email = '';
        this.loginDetails.password = '';
        this.message = 'Invalid email or password';
      }
    },
  },
};

</script>
