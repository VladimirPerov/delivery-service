<script setup>
import axios from 'axios';
import { onBeforeMount, ref } from 'vue';

const categories = ref([]);

const categoryToAdd = ref({
  name: '',
  description: ''
});

const categoryToEdit = ref({});

async function fetchCategories() {
  const r = await axios.get("/api/categories/");
  categories.value = r.data;
}

async function onCategoryAdd() {
  await axios.post("/api/categories/", categoryToAdd.value);
  categoryToAdd.value = {
    name: '',
    description: ''
  };
  await fetchCategories();
}

function onCategoryEditClick(category) {
  categoryToEdit.value = { ...category };
}

async function onUpdateCategory() {
  await axios.put(`/api/categories/${categoryToEdit.value.id}/`, categoryToEdit.value);
  await fetchCategories();
}

async function onRemoveClick(category) {
  await axios.delete(`/api/categories/${category.id}/`);
  await fetchCategories();
}

onBeforeMount(async () => {
  await fetchCategories();
});
</script>

<template>
  <div class="container my-4">
    <h2>Управление категориями</h2>

    <form @submit.prevent.stop="onCategoryAdd" class="card p-3 mb-4 shadow-sm">
      <h5 class="mb-3">Добавить новую категорию</h5>
      <div class="row g-3">
        <div class="col-12">
          <div class="form-floating">
            <input 
              type="text" 
              class="form-control" 
              v-model="categoryToAdd.name" 
              required 
              id="newCatName" 
              placeholder="Название" 
            />
            <label for="newCatName">Название категории</label>
          </div>
        </div>

        <div class="col-12">
          <div class="form-floating">
            <textarea 
              class="form-control" 
              v-model="categoryToAdd.description" 
              id="newCatDesc" 
              style="height: 100px" 
              placeholder="Описание"
            ></textarea>
            <label for="newCatDesc">Описание</label>
          </div>
        </div>

        <div class="col-12">
          <button class="btn btn-primary w-100">Добавить категорию</button>
        </div>
      </div>
    </form>

    <div class="card shadow-sm">
      <div class="card-body">
        <div v-if="categories.length === 0" class="text-center text-muted py-3">
          Категории не найдены.
        </div>
        <div 
          v-for="item in categories" 
          :key="item.id" 
          class="d-flex justify-content-between align-items-center border-bottom py-2"
        >
          <div>
            <strong>{{ item.name }}</strong>
            <p class="text-muted mb-0 small" v-if="item.description">
              {{ item.description }}
            </p>
          </div>
          <div class="btn-group">
            <button
              class="btn btn-outline-success btn-sm"
              @click="onCategoryEditClick(item)"
              data-bs-toggle="modal"
              data-bs-target="#editCategoryModal">
              Изменить
            </button>
            <button class="btn btn-outline-danger btn-sm" @click="onRemoveClick(item)">
              Удалить
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="modal fade" id="editCategoryModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title fs-5">Редактировать категорию</h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <div class="form-floating">
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="categoryToEdit.name" 
                  id="editCatName" 
                  placeholder="Название" 
                />
                <label for="editCatName">Название</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <textarea 
                  class="form-control" 
                  v-model="categoryToEdit.description" 
                  id="editCatDesc" 
                  style="height: 100px" 
                  placeholder="Описание"
                ></textarea>
                <label for="editCatDesc">Описание</label>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
            <button data-bs-dismiss="modal" type="button" class="btn btn-primary" @click="onUpdateCategory">
              Сохранить
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<style>
</style>