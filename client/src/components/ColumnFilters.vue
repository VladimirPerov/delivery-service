<script setup>
defineProps({ fields: Array });
const emit = defineEmits(['apply']);

function apply(form) {
  const filters = {};
  for (const [name, value] of new FormData(form)) {
    if (value.trim()) filters[name] = value.trim();
  }
  emit('apply', filters);
}
</script>

<template>
  <form class="row g-2 align-items-end mb-3" aria-label="Фильтры списка"
        @submit.prevent="apply($event.target)" @reset="emit('apply', {})">
    <label v-for="field in fields" :key="field.name" class="col-sm-6 col-lg-3">
      {{ field.label }}
      <select v-if="field.options" :name="field.name" class="form-select">
        <option value="">Все</option>
        <option v-for="(label, value) in field.options" :key="value" :value="value">{{ label }}</option>
      </select>
      <input v-else :name="field.name" :type="field.type || 'text'" :step="field.step"
             class="form-control" />
    </label>
    <div class="col-auto">
      <button type="submit" class="btn btn-primary me-2">Применить</button>
      <button type="reset" class="btn btn-outline-secondary">Сбросить</button>
    </div>
  </form>
</template>
