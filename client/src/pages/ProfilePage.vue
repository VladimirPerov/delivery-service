<script setup>
import axios from 'axios';
import { onBeforeMount, ref, watch } from 'vue';
import UserFilter from '@/components/UserFilter.vue';

const profiles = ref([]);
const selectedUser = ref("");
const stats = ref(null);

async function fetchProfiles() {
    const params = { user: selectedUser.value };
    const [list, summary] = await Promise.all([
        axios.get('/api/profiles/', { params }),
        axios.get('/api/profiles/stats/', { params }),
    ]);
    if (params.user !== selectedUser.value) return;
    profiles.value = list.data;
    stats.value = summary.data;
}

onBeforeMount(fetchProfiles);
watch(selectedUser, fetchProfiles);
</script>

<template>
    <div class="container my-4">
        <h2>Профили</h2>
        <UserFilter v-model="selectedUser" />
        <p v-if="stats" class="text-muted">
            Всего профилей: {{ stats.total }} · Клиентов: {{ stats.clients }} · Курьеров: {{ stats.couriers }}
        </p>
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
