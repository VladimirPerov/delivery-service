<script setup>
import axios from 'axios';
import { onBeforeMount, ref, watch } from 'vue';
import UserFilter from '@/components/UserFilter.vue';

const profiles = ref([]);
const selectedUser = ref("");

async function fetchProfiles() {
    const r = await axios.get('/api/profiles/', { params: { user: selectedUser.value } });
    profiles.value = r.data;
}

onBeforeMount(fetchProfiles);
watch(selectedUser, fetchProfiles);
</script>

<template>
    <div class="container my-4">
        <h2>Профили</h2>
        <UserFilter v-model="selectedUser" />
        <div v-for="profile in profiles" :key="profile.id" class="card p-3 mb-3">
            <div>Пользователь: {{ profile.user }}</div>
            <div>Имя: {{ profile.name }}</div>
            <div>Телефон: {{ profile.phone }}</div>
            <div>Бонусные баллы: {{ profile.bonus_points }}</div>
        </div>
    </div>
</template>

<style>
</style>
