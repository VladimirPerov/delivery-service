<script setup>
import { computed } from 'vue';

const props = defineProps({
  page: Number,
  total: Number,
});
const emit = defineEmits(['change']);
const pagesCount = computed(() => Math.ceil(props.total / 10));
</script>

<template>
  <nav v-if="pagesCount > 1" class="my-3" aria-label="Страницы списка">
    <ul class="pagination justify-content-center">
      <li class="page-item">
        <button class="page-link" :disabled="page === 1" @click="emit('change', page - 1)">Назад</button>
      </li>
      <li class="page-item"><span class="page-link">Страница {{ page }} из {{ pagesCount }}</span></li>
      <li class="page-item">
        <button class="page-link" :disabled="page === pagesCount" @click="emit('change', page + 1)">Вперёд</button>
      </li>
    </ul>
  </nav>
</template>
