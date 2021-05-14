import Vue from 'vue';
import VueRouter from 'vue-router';
import store from '../store';

Vue.use(VueRouter);

const routes = [
  {
    path: '/',
    name: 'Login',
    component: () => import('../views/Login.vue'),
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('../views/Home.vue'),
  },
  {
    path: '/apps',
    name: 'Apps',
    component: () => import('../views/Apps.vue'),
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('../views/Reports.vue'),
  },
  {
    path: '/manage-users',
    name: 'Users',
    component: () => import('../views/Users.vue'),
  },
  {
    path: '/files-and-logs',
    name: 'Logs',
    component: () => import('../views/Logs.vue'),
  },
];

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes,
});

router.beforeEach((to, from, next) => {
  // redirect to login page if not logged in and trying to access a restricted page
  const publicPages = ['/'];
  const authRequired = !publicPages.includes(to.path);
  const loggedIn = store.state.token;
  return authRequired && !loggedIn ? next('/') : next();
});

export default router;
