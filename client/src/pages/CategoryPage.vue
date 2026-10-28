<script setup>
import axios from 'axios';
import UserFilter from '@/components/UserFilter.vue';
import { onBeforeMount, ref, watch } from 'vue';

const selectedUser = ref("");

const categories = ref([]);

const categoryToAdd = ref({
  name: '',
  description: ''
});

const categoryToEdit = ref({});

const categoriesPictureRef = ref();
const categoryAddImageUrl = ref();

const categoryEditPictureRef = ref();
const categoryEditImageUrl = ref();

const activeImageModalUrl = ref(null);

function openImageModal(url) {
  activeImageModalUrl.value = url;
}

async function categoryEditPictureChange() {
  categoryEditImageUrl.value = URL.createObjectURL(categoryEditPictureRef.value.files[0]);
}

async function categoryAddPictureChange() {
  categoryAddImageUrl.value = URL.createObjectURL(categoriesPictureRef.value.files[0]);
}

async function fetchCategories() {
  const r = await axios.get("/api/categories/", { params: { user: selectedUser.value } });
  categories.value = r.data;
}

async function onCategoryAdd() {
  const formData = new FormData();

  formData.append('picture', categoriesPictureRef.value.files[0]);

  formData.set('name', categoryToAdd.value.name);
  formData.set('description', categoryToAdd.value.description);

  await axios.post("/api/categories/", formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
  
  categoryToAdd.value = {
    name: '',
    description: ''
  };
  await fetchCategories();
}

function onCategoryEditClick(category) {
  categoryToEdit.value = { ...category };

  categoryEditPictureRef.value.value = '';
  categoryEditImageUrl.value = null;
}

async function onUpdateCategory() {
  const formData = new FormData();

  if (categoryEditPictureRef.value?.files[0]) {
    formData.append('picture', categoryEditPictureRef.value.files[0]);
  }

  formData.set('name', categoryToEdit.value.name);
  formData.set('description', categoryToEdit.value.description || '');

  await axios.put(`/api/categories/${categoryToEdit.value.id}/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });

  if (categoryEditPictureRef.value) categoryEditPictureRef.value.value = '';
  categoryEditImageUrl.value = null;

  await fetchCategories();
}

async function onRemoveClick(category) {
  await axios.delete(`/api/categories/${category.id}/`);
  await fetchCategories();
}

onBeforeMount(async () => {
  await fetchCategories();
});
watch(selectedUser, fetchCategories);
</script>

<template>
  <div class="container my-4">
    <h2>Управление категориями</h2>
    <UserFilter v-model="selectedUser" />

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
            <label for="newCatPicture" class="form-label">Изображение категории</label>
            <input class="form-control" type="file" id="newCatPicture"ref="categoriesPictureRef" @change="categoryAddPictureChange"accept="image/*">
          </div>

          <div class="col-12" v-if="categoryAddImageUrl">
            <img :src="categoryAddImageUrl" style="max-height: 100px; cursor: pointer;" alt="Превью" class="img-thumbnail" @click="openImageModal(categoryAddImageUrl)" data-bs-toggle="modal" data-bs-target="#categoryImageModal">
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

            <div v-show="item.picture" class="mt-2">
              <img :src="item.picture" style="max-height: 100px; cursor: pointer;" alt="Фото категории" class="img-thumbnail" @click="openImageModal(item.picture)" data-bs-toggle="modal" data-bs-target="#categoryImageModal">
            </div>

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
                  placeholder="Описание">
                </textarea>
                <label for="editCatDesc">Описание</label>
              </div>
            </div>

            <div class="mb-3">
              <label for="editCatPicture" class="form-label">Изменить изображение категории</label>
              <input class="form-control" type="file" ref="categoryEditPictureRef" @change="categoryEditPictureChange" id="editCatPicture" accept="image/*">
            </div>

            <div class="mb-3" v-if="categoryEditImageUrl || categoryToEdit.picture">
              <label class="form-label d-block">Предпросмотр:</label>
              <img :src="categoryEditImageUrl || categoryToEdit.picture" style="max-height: 100px; cursor: pointer;" alt="Превью" class="img-thumbnail" @click="openImageModal(categoryEditImageUrl || categoryToEdit.picture)" data-bs-toggle="modal" data-bs-target="#categoryImageModal">
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

    <div class="modal fade" id="categoryImageModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content bg-transparent border-0">
          <div class="modal-header border-0 pb-0">
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body text-center p-0">
            <img :src="activeImageModalUrl" class="img-fluid rounded shadow" alt="Увеличенное изображение" style="max-height: 80vh; object-fit: contain;">
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
</style>