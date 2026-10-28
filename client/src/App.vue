<script setup>
import NavBar from './components/NavBar.vue'
import useProfileStore from './stores/profileStore'
import { storeToRefs } from 'pinia'

const profileStore = useProfileStore();
const { isAuthenticated, userName } = storeToRefs(profileStore);
</script>

<template>
  <nav-bar></nav-bar>
  <div>
    <router-view v-if="isAuthenticated || $route.path === '/login' || $route.path === '/'" :key="userName"></router-view>
    <div v-else class="container">
      Для просмотра данных <router-link to="/login">войдите в приложение</router-link>.
    </div>
  </div>
</template>
<style scoped></style>
