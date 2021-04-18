import Vue from 'vue';
import Vuex from 'vuex';
import createPersistedState from 'vuex-persistedstate';
import axios from 'axios';

Vue.use(Vuex);

const getDefaultState = () => ({
  token: '',
  user: {},
});

export default new Vuex.Store({
  plugins: [createPersistedState()],
  state: getDefaultState(),
  getters: {
    isLoggedIn: (state) => state.token,
    getUser: (state) => state.user,
    isAdmin: (state) => state.user.role === 'admin',
    getToken: (state) => state.token,
  },
  mutations: {
    SET_TOKEN: (state, token) => {
      state.token = token;
    },
    SET_USER: (state, user) => {
      state.user = user;
    },
    RESET: (state) => {
      Object.assign(state, getDefaultState());
    },
  },
  actions: {
    // eslint-disable-next-line no-unused-vars
    login: ({ commit, dispatch }, { token, user }) => {
      axios.defaults.headers.common.Authorization = `Bearer ${token}`;
      commit('SET_TOKEN', token);
      commit('SET_USER', user);
    },
    logout: ({ commit }) => {
      commit('RESET', '');
    },
  },
});
