<template>
  <div>
    <admin-dash v-if="isAdmin()"></admin-dash>
    <user-dash v-else></user-dash>
  </div>
</template>

<script>
import UserDash from '../components/UserDash.vue';
import AdminDash from '../components/AdminDash.vue';

export default {
  components: {
    UserDash,
    AdminDash,
  },
  data() {
    return {
      role: '',
    };
  },
  created() {
    this.role = this.$store.getters.getUser.role;
  },
  methods: {
    isAdmin() {
      return this.role === 'admin';
    },
  },
};
</script>
