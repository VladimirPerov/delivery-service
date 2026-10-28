<script setup>
import axios from 'axios';
import { ref, watch } from 'vue';
import { storeToRefs } from 'pinia';
import useProfileStore from '@/stores/profileStore';

defineProps(['modelValue']);
const emit = defineEmits(['update:modelValue']);
const profileStore = useProfileStore();
const { isSuperuser } = storeToRefs(profileStore);
const users = ref([]);

watch(isSuperuser, async () => {
    if (isSuperuser.value) {
        const r = await axios.get('/api/users/');
        users.value = r.data;
    }
}, { immediate: true });
</script>

<template>
    <div v-if="isSuperuser" class="mb-3">
        <label class="form-label">
            Пользователь
            <select class="form-select" :value="modelValue" @change="emit('update:modelValue', $event.target.value)">
                <option value="">Все пользователи</option>
                <option v-for="user in users" :key="user.id" :value="user.id">{{ user.username }}</option>
            </select>
        </label>
    </div>
</template>
