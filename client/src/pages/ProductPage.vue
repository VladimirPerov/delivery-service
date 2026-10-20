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

async function fetchProducts() {
  const r = await axios.get("/api/products/");
  products.value = r.data;
}

async function fetchCategories() {
  const r = await axios.get("/api/categories/");
  categories.value = r.data;
}

async function onProductAdd() {
    await axios.post("/api/products/", productToAdd.value);
    
    productToAdd.value = {
      product_type: 'unit',
      price: '0.00',
      stock_quantity: '0.00',
      description: ''
    };
    await fetchProducts();
}

function onProductEditClick(product) {
  productToEdit.value = { ...product };
}

async function onUpdateProduct() {
    await axios.put(`/api/products/${productToEdit.value.id}/`, productToEdit.value);
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
          <button class="btn btn-primary w-100">Добавить продукт</button>
        </div>
      </div>
    </form>

    <div class="card shadow-sm">
      <div class="card-body">
        <div v-for="item in products" :key="item.id" class="d-flex justify-content-between align-items-center border-bottom py-2">
          <div>
            <strong>{{ item.name }}</strong> — {{ item.price }} руб. 
            <small class="text-muted">(Остаток: {{ item.stock_quantity }})</small>
          </div>
          <div class="btn-group">
            <button
              class="btn btn-outline-success btn-sm"
              @click="onProductEditClick(item)"
              data-bs-toggle="modal"
              data-bs-target="#editProductModal">
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

  </div>
</template>

<style>
</style>