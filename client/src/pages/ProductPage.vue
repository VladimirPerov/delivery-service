<script setup>
import axios from 'axios';
import { nextTick, onBeforeMount, onBeforeUnmount, ref } from 'vue';

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
const productAddPreviewUrls = ref([]);
const productEditPreviewUrls = ref([]);

const activeImageModalUrls = ref([]);
const activeImageModalIndex = ref(0);
const isImageModalOpen = ref(false);
const imageModalRef = ref(null);

function getProductPictures(product) {
  return (product.pictures || []).map(picture => picture.picture).filter(Boolean);
}

function clearPreviews(previewUrls) {
  previewUrls.value.forEach(url => URL.revokeObjectURL(url));
  previewUrls.value = [];
}

function updatePreviews(event, previewUrls) {
  clearPreviews(previewUrls);
  previewUrls.value = Array.from(event.target.files || [])
    .filter(file => file.type.startsWith('image/'))
    .map(file => URL.createObjectURL(file));
}

function onAddPicturesChange(event) {
  updatePreviews(event, productAddPreviewUrls);
}

function onEditPicturesChange(event) {
  updatePreviews(event, productEditPreviewUrls);
}

async function openImageModal(urls, index = 0) {
  if (!urls.length) return;
  activeImageModalUrls.value = [...urls];
  activeImageModalIndex.value = index;
  isImageModalOpen.value = true;
  await nextTick();
  imageModalRef.value?.focus();
}

function closeImageModal() {
  isImageModalOpen.value = false;
}

function showAdjacentImage(step) {
  const length = activeImageModalUrls.value.length;
  if (length > 1) {
    activeImageModalIndex.value = (activeImageModalIndex.value + step + length) % length;
  }
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
    clearPreviews(productAddPreviewUrls);

    await fetchProducts();
}

function onProductEditClick(product) {
  productToEdit.value = { ...product };

  productEditPicturesRef.value.value = '';
  clearPreviews(productEditPreviewUrls);
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
    clearPreviews(productEditPreviewUrls);

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

onBeforeUnmount(() => {
  clearPreviews(productAddPreviewUrls);
  clearPreviews(productEditPreviewUrls);
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
          <label for="newPictures" class="form-label">Фотографии продукта</label>
          <input class="form-control" type="file" ref="productAddPicturesRef" id="newPictures" accept="image/*" multiple @change="onAddPicturesChange">
        </div>

        <div v-if="productAddPreviewUrls.length" class="col-12">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="fw-semibold">Предпросмотр фотографий</span>
            <span class="badge text-bg-light">{{ productAddPreviewUrls.length }} фото</span>
          </div>
          <div class="product-gallery">
            <button v-for="(url, index) in productAddPreviewUrls" :key="url" type="button" class="product-gallery-item" :aria-label="`Увеличить фото ${index + 1}`" @click="openImageModal(productAddPreviewUrls, index)">
              <img :src="url" :alt="`Новое фото ${index + 1}`">
            </button>
          </div>
        </div>

        <div class="col-12">
          <button class="btn btn-primary w-100">Добавить продукт</button>
        </div>
      </div>
    </form>

    <div class="card shadow-sm">
      <div class="card-body">
        <div v-for="item in products" :key="item.id" class="d-flex justify-content-between align-items-center gap-3 border-bottom py-3">
            
            <div class="d-flex align-items-center gap-3 product-list-main"> 
                
                <button v-if="getProductPictures(item).length" type="button" class="product-list-image" :aria-label="`Просмотреть фотографии: ${item.name}`" @click="openImageModal(getProductPictures(item))">
                  <img :src="getProductPictures(item)[0]" :alt="`Фото продукта ${item.name}`">
                  <span v-if="getProductPictures(item).length > 1" class="photo-count">+{{ getProductPictures(item).length - 1 }}</span>
                </button>
                <div v-else class="product-list-placeholder">Нет фото</div>

                <div>
                  <strong>{{ item.name }}</strong>
                  <div>{{ item.price }} руб.</div>
                  <small class="text-muted">Остаток: {{ item.stock_quantity }}</small>
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
              <input class="form-control" type="file" ref="productEditPicturesRef" id="editPictures" accept="image/*" multiple @change="onEditPicturesChange">
            </div>

            <div v-if="getProductPictures(productToEdit).length" class="mb-3">
              <div class="fw-semibold mb-2">Сохранённые фотографии</div>
              <div class="product-gallery">
                <button v-for="(url, index) in getProductPictures(productToEdit)" :key="url" type="button" class="product-gallery-item" :aria-label="`Увеличить сохранённое фото ${index + 1}`" @click="openImageModal(getProductPictures(productToEdit), index)">
                  <img :src="url" :alt="`Сохранённое фото ${index + 1}`">
                </button>
              </div>
            </div>

            <div v-if="productEditPreviewUrls.length" class="mb-3">
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="fw-semibold">Новые фотографии</span>
                <span class="badge text-bg-light">{{ productEditPreviewUrls.length }} фото</span>
              </div>
              <div class="product-gallery">
                <button v-for="(url, index) in productEditPreviewUrls" :key="url" type="button" class="product-gallery-item" :aria-label="`Увеличить новое фото ${index + 1}`" @click="openImageModal(productEditPreviewUrls, index)">
                  <img :src="url" :alt="`Новое фото ${index + 1}`">
                </button>
              </div>
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
    <Teleport to="body">
      <div v-if="isImageModalOpen" ref="imageModalRef" class="product-lightbox" role="dialog" aria-modal="true" aria-label="Просмотр фотографий продукта" tabindex="-1" @click.self="closeImageModal" @keydown.esc.prevent.stop="closeImageModal" @keydown.left.prevent.stop="showAdjacentImage(-1)" @keydown.right.prevent.stop="showAdjacentImage(1)">
        <button type="button" class="product-lightbox-close" aria-label="Закрыть предпросмотр" @click="closeImageModal">&times;</button>
        <div class="product-lightbox-content">
          <button v-if="activeImageModalUrls.length > 1" type="button" class="product-lightbox-arrow" aria-label="Предыдущее фото" @click="showAdjacentImage(-1)">‹</button>
          <img :src="activeImageModalUrls[activeImageModalIndex]" :alt="`Фото ${activeImageModalIndex + 1}`" class="product-lightbox-image">
          <button v-if="activeImageModalUrls.length > 1" type="button" class="product-lightbox-arrow" aria-label="Следующее фото" @click="showAdjacentImage(1)">›</button>
        </div>
        <div v-if="activeImageModalUrls.length > 1" class="product-lightbox-count">{{ activeImageModalIndex + 1 }} / {{ activeImageModalUrls.length }}</div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.product-list-main {
  min-width: 0;
}

.product-list-image,
.product-list-placeholder {
  position: relative;
  display: grid;
  place-items: center;
  flex: 0 0 96px;
  width: 96px;
  height: 96px;
  padding: 0;
  border: 1px solid #dee2e6;
  border-radius: 12px;
  background: #f8f9fa;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, .08);
}

.product-list-image,
.product-gallery-item {
  cursor: zoom-in;
}

.product-list-image img,
.product-gallery-item img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-list-placeholder {
  color: #6c757d;
  font-size: .75rem;
}

.photo-count {
  position: absolute;
  right: 5px;
  bottom: 5px;
  padding: 2px 7px;
  border-radius: 20px;
  background: rgba(0, 0, 0, .75);
  color: white;
  font-size: .75rem;
}

.product-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
}

.product-gallery-item {
  aspect-ratio: 1;
  padding: 4px;
  border: 1px solid #dee2e6;
  border-radius: 12px;
  background: white;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, .06);
  transition: transform .15s ease, box-shadow .15s ease;
}

.product-gallery-item img {
  border-radius: 8px;
}

.product-list-image:hover,
.product-gallery-item:hover {
  box-shadow: 0 4px 14px rgba(0, 0, 0, .17);
}

.product-gallery-item:hover {
  transform: translateY(-2px);
}

.product-list-image:focus-visible,
.product-gallery-item:focus-visible {
  outline: 3px solid #0d6efd;
  outline-offset: 2px;
}

.product-lightbox {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 50px 20px 20px;
  background: rgba(10, 15, 25, .94);
}

.product-lightbox-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  min-height: 0;
}

.product-lightbox-image {
  display: block;
  max-width: min(100%, 1100px);
  max-height: 78vh;
  min-width: 0;
  object-fit: contain;
  border-radius: 10px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, .35);
}

.product-lightbox-close,
.product-lightbox-arrow {
  border: 1px solid rgba(255, 255, 255, .25);
  border-radius: 50%;
  color: white;
  background: rgba(255, 255, 255, .14);
  cursor: pointer;
}

.product-lightbox-close {
  position: absolute;
  top: 15px;
  right: 20px;
  width: 42px;
  height: 42px;
  font-size: 28px;
  line-height: 1;
}

.product-lightbox-arrow {
  flex: 0 0 42px;
  width: 42px;
  height: 42px;
  font-size: 30px;
  line-height: 1;
}

.product-lightbox-close:hover,
.product-lightbox-arrow:hover {
  background: rgba(255, 255, 255, .3);
}

.product-lightbox-count {
  color: white;
  font-size: .9rem;
}

@media (max-width: 575px) {
  .product-list-image,
  .product-list-placeholder {
    flex-basis: 76px;
    width: 76px;
    height: 76px;
  }

  .product-lightbox {
    padding-inline: 8px;
  }

  .product-lightbox-content {
    gap: 5px;
  }

  .product-lightbox-arrow {
    flex-basis: 32px;
    width: 32px;
    height: 36px;
  }
}
</style>
