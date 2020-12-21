<template>
  <nav class="navbar navbar-expand-lg navbar-light bg-light">
    <div class="container">
      <a class="navbar-brand" href="#">Call Link Uganda</a>
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
          <li class="nav-item">
            <router-link to="/" class="nav-link">Home</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/apps" class="nav-link">Apps</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/reports" class="nav-link">Reports</router-link>
          </li>
<!--          <li class="nav-item">-->
<!--            <router-link to="/configuration" class="nav-link">Configuration</router-link>-->
<!--          </li>-->
        </ul>
        <ul class="navbar-nav">
          <li class="nav-item">
            <router-link to="/profile" class="nav-link">Admin</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/logout" class="nav-link">Logout</router-link>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'NavBar',
};
</script>
