<script setup>
import axios from 'axios';
import { onBeforeMount, ref, watch } from 'vue';
import Pagination from '@/components/Pagination.vue';
import UserFilter from '@/components/UserFilter.vue';

const profiles = ref([]);
const page = ref(1);
const total = ref(0);
const selectedUser = ref("");
const stats = ref(null);

async function fetchProfiles(newPage = page.value) {
    page.value = newPage;
    const params = { user: selectedUser.value, page: newPage };
    const [list, summary] = await Promise.all([
        axios.get('/api/profiles/', { params }),
        axios.get('/api/profiles/stats/', { params }),
    ]);
    if (params.user !== selectedUser.value || newPage !== page.value) return;
    profiles.value = list.data.results;
    total.value = list.data.count;
    stats.value = summary.data;
}

onBeforeMount(fetchProfiles);
watch(selectedUser, () => fetchProfiles(1));
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
        <Pagination :page="page" :total="total" @change="fetchProfiles" />
    </div>
</template>

<style>
</style>
