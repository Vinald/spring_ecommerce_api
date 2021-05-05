<template>
  <nav class="navbar navbar-dark navbar-expand-lg" style="background-color: #AD1927;">
    <div class="container">
      <a class="navbar-brand" href="#">Academy IVR</a>
      <button
        class="navbar-toggler"
        type="button"
        data-toggle="collapse"
        data-target="#navbarSupportedContent"
        aria-controls="navbarSupportedContent"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav mr-auto">
          <li class="nav-item" v-if="isLoggedIn">
            <router-link to="/home" class="nav-link" active-class="active">Home</router-link>
          </li>
          <li class="nav-item" v-if="isLoggedIn">
            <router-link to="/apps" class="nav-link" active-class="active">Apps</router-link>
          </li>
          <li class="nav-item" v-if="isLoggedIn">
            <router-link to="/reports" class="nav-link" active-class="active">Reports</router-link>
          </li>
          <li class="nav-item" v-if="isLoggedIn">
            <router-link to="/files-and-logs" class="nav-link" active-class="active">Files & Logs</router-link>
          </li>
          <li class="nav-item" v-if="isAdmin">
            <router-link to="/manage-users" class="nav-link" active-class="active">Manage users</router-link>
          </li>
        </ul>
        <ul class="navbar-nav">
          <li class="nav-item">
            <router-link to="#" class="nav-link">{{ email }}
              <span v-if="isAdmin"> ({{ role }})</span>
            </router-link>
          </li>
          <li class="nav-item" v-if="isLoggedIn === false">
            <router-link to="/" class="nav-link">Login</router-link>
          </li>
          <b-nav-item v-if="isLoggedIn" @click="logout">Logout</b-nav-item>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'NavBar',
  data() {
    return {
      role: '',
      email: '',
      isAdmin: false,
      isLoggedIn: false,
    };
  },
  created() {
    this.role = this.$store.getters.getUser.role;
    this.email = this.$store.getters.getUser.email;
    this.isAdmin = this.role === 'admin';
    this.isLoggedIn = this.$store.getters.isLoggedIn;
  },
  methods: {
    logout() {
      this.$store.dispatch('logout');
      this.$router.push('/');
    },
  },
};
</script>
