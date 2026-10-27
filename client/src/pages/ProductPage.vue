<script setup>
import axios from 'axios';
import { onBeforeMount, ref } from 'vue';

const products = ref([]);
const categories = ref([]);

const productToAdd = ref({
  product_type: 'unit',
  price: '0.00',
  stock_quantity: '0.00',
  description: ''
});

const productToEdit = ref({});

const productAddPicturesRef = ref();
const productEditPicturesRef = ref();

const activeImageModalUrls = ref([]);
const activeImageModalIndex = ref(0);

function getProductPictures(product) {
  return (product.pictures || []).map(picture => picture.picture);
}

function openImageModal(urls) {
  activeImageModalUrls.value = urls;
  activeImageModalIndex.value = 0;
}

async function uploadProductPictures(productId, files) {
  for (const file of files) {
    const formData = new FormData();
    formData.append('product', productId);
    formData.append('picture', file);
    await axios.post("/api/product-pictures/", formData);
  }
}

async function fetchProducts() {
  const r = await axios.get("/api/products/");
  products.value = r.data;
}

async function fetchCategories() {
  const r = await axios.get("/api/categories/");
  categories.value = r.data;
}

async function onProductAdd() {
    const formData = new FormData();

    formData.set('name', productToAdd.value.name);
    formData.set('category', productToAdd.value.category);
    formData.set('description', productToAdd.value.description);
    formData.set('price', productToAdd.value.price);
    formData.set('stock_quantity', productToAdd.value.stock_quantity);
    formData.set('product_type', productToAdd.value.product_type);

    const r = await axios.post("/api/products/", formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    });

    await uploadProductPictures(r.data.id, productAddPicturesRef.value.files);
    
    productToAdd.value = {
      product_type: 'unit',
      price: '0.00',
      stock_quantity: '0.00',
      description: ''
    };

    productAddPicturesRef.value.value = '';

    await fetchProducts();
}

function onProductEditClick(product) {
  productToEdit.value = { ...product };

  productEditPicturesRef.value.value = '';
}

async function onUpdateProduct() {
    const formData = new FormData();

    formData.set('name', productToEdit.value.name);
    if (productToEdit.value.category) {
        formData.set('category', productToEdit.value.category);
    }
    formData.set('description', productToEdit.value.description || '');
    formData.set('price', productToEdit.value.price);
    formData.set('stock_quantity', productToEdit.value.stock_quantity);
    formData.set('product_type', productToEdit.value.product_type);

    await axios.put(`/api/products/${productToEdit.value.id}/`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    });

    await uploadProductPictures(productToEdit.value.id, productEditPicturesRef.value.files);

    productEditPicturesRef.value.value = '';

    await fetchProducts();
}

async function onRemoveClick(product) {
    await axios.delete(`/api/products/${product.id}/`);
    await fetchProducts();
}

onBeforeMount(async () => {
  await fetchCategories();
  await fetchProducts();
});
</script>

<template>
  <div class="container my-4">
    <h2>Управление продуктами</h2>

    <form @submit.prevent.stop="onProductAdd" class="card p-3 mb-4 shadow-sm">
      <h5 class="mb-3">Добавить новый продукт</h5>
      <div class="row g-3">
        <div class="col-md-6">
          <div class="form-floating">
            <input type="text" class="form-control" v-model="productToAdd.name" required id="newName" placeholder="Название" />
            <label for="newName">Название</label>
          </div>
        </div>
        
        <div class="col-md-6">
          <div class="form-floating">
            <select class="form-select" v-model="productToAdd.category" required id="newCat">
              <option :value="null" disabled>Выберите категорию</option>
              <option :value="c.id" v-for="c in categories" :key="c.id">{{ c.name }}</option>
            </select>
            <label for="newCat">Категория</label>
          </div>
        </div>

        <div class="col-12">
          <div class="form-floating">
            <textarea class="form-control" v-model="productToAdd.description" id="newDesc" style="height: 80px" placeholder="Описание"></textarea>
            <label for="newDesc">Описание</label>
          </div>
        </div>

        <div class="col-md-4">
          <div class="form-floating">
            <input type="number" step="0.01" class="form-control" v-model="productToAdd.price" id="newPrice" placeholder="Цена" />
            <label for="newPrice">Цена</label>
          </div>
        </div>

        <div class="col-md-4">
          <div class="form-floating">
            <input type="number" step="0.01" class="form-control" v-model="productToAdd.stock_quantity" id="newStock" placeholder="Остаток" />
            <label for="newStock">Остаток на складе</label>
          </div>
        </div>

        <div class="col-md-4">
          <div class="form-floating">
            <select class="form-select" v-model="productToAdd.product_type" id="newType">
              <option value="unit">Штучный</option>
              <option value="weight">Весовой</option>
            </select>
            <label for="newType">Тип товара</label>
          </div>
        </div>

        <div class="col-12">
          <label for="newPictures" class="form-label">Фотографии альбома</label>
          <input class="form-control" type="file" ref="productAddPicturesRef" id="newPictures" accept="image/*" multiple>
        </div>

        <div class="col-12">
          <button class="btn btn-primary w-100">Добавить продукт</button>
        </div>
      </div>
    </form>

    <div class="card shadow-sm">
      <div class="card-body">
        <div v-for="item in products" :key="item.id" class="d-flex justify-content-between align-items-center border-bottom py-2">
            
            <div class="d-flex align-items-center"> 
                
                <div v-if="getProductPictures(item).length" class="me-3">
                <img :src="getProductPictures(item)[0]" style="max-height: 60px; cursor: pointer;" alt="Фото продукта" @click="openImageModal(getProductPictures(item))" data-bs-toggle="modal" data-bs-target="#imagePreviewModal">
                </div>

                <div>
                <strong>{{ item.name }}</strong> — {{ item.price }} руб. 
                <small class="text-muted">(Остаток: {{ item.stock_quantity }})</small>
                </div>
                
            </div>

            <div class="btn-group">
                <button class="btn btn-outline-success btn-sm" @click="onProductEditClick(item)" data-bs-toggle="modal" data-bs-target="#editProductModal">
                Изменить
                </button>
                <button class="btn btn-outline-danger btn-sm" @click="onRemoveClick(item)">
                Удалить
                </button>
            </div>
        </div>
      </div>
    </div>

    <div class="modal fade" id="editProductModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title fs-5">Редактировать продукт</h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <div class="form-floating">
                <input type="text" class="form-control" v-model="productToEdit.name" id="editName" placeholder="Название" />
                <label for="editName">Название</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <select class="form-select" v-model="productToEdit.category" id="editCat">
                  <option :value="null">Без категории</option>
                  <option :value="c.id" v-for="c in categories" :key="c.id">{{ c.name }}</option>
                </select>
                <label for="editCat">Категория</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <textarea class="form-control" v-model="productToEdit.description" id="editDesc" style="height: 80px" placeholder="Описание"></textarea>
                <label for="editDesc">Описание</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <input type="number" step="0.01" class="form-control" v-model="productToEdit.price" id="editPrice" placeholder="Цена" />
                <label for="editPrice">Цена</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <input type="number" step="0.01" class="form-control" v-model="productToEdit.stock_quantity" id="editStock" placeholder="Остаток" />
                <label for="editStock">Остаток на складе</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <select class="form-select" v-model="productToEdit.product_type" id="editType">
                  <option value="unit">Штучный</option>
                  <option value="weight">Весовой</option>
                </select>
                <label for="editType">Тип товара</label>
              </div>
            </div>

            <div class="mb-3">
              <label for="editPictures" class="form-label">Добавить фотографии в альбом</label>
              <input class="form-control" type="file" ref="productEditPicturesRef" id="editPictures" accept="image/*" multiple>
            </div>

          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
            <button data-bs-dismiss="modal" type="button" class="btn btn-primary" @click="onUpdateProduct">
              Сохранить
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal fade" id="imagePreviewModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content bg-transparent border-0">
          <div class="modal-header border-0 pb-0">
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body text-center p-0">
            <img :src="activeImageModalUrls[activeImageModalIndex]" class="img-fluid rounded shadow" alt="Увеличенное изображение" style="max-height: 80vh; object-fit: contain;">
            <div v-if="activeImageModalUrls.length > 1" class="d-flex justify-content-center align-items-center gap-3 mt-3">
              <button type="button" class="btn btn-light" @click="activeImageModalIndex = (activeImageModalIndex + activeImageModalUrls.length - 1) % activeImageModalUrls.length">Назад</button>
              <span class="text-white">{{ activeImageModalIndex + 1 }} / {{ activeImageModalUrls.length }}</span>
              <button type="button" class="btn btn-light" @click="activeImageModalIndex = (activeImageModalIndex + 1) % activeImageModalUrls.length">Вперёд</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
</style>