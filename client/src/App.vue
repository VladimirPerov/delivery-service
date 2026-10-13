<script setup>

import axios from 'axios';
import { onBeforeMount, ref } from 'vue';
import Cookies from 'js-cookie';

const products = ref([]);
const categories = ref([]);
const productToAdd = ref({});

async function fetchProducts() {
  const r = await axios.get("/api/products/");
  console.log(r.data);
  products.value = r.data;
}

async function fetchCategories() {
  const r = await axios.get("/api/categories/");
  categories.value = r.data;
}

async function onProductAdd() {
  try {
    await axios.post("/api/products/", {
      description: "Без описания",
      price: "0.00",
      stock_quantity: "0.00",
      product_type: "unit",
      ...productToAdd.value,
    });
    productToAdd.value = {};
    await fetchProducts();
  } catch (error) {
    console.error("Ошибка валидации бэкенда:", error.response?.data);
  }
}

onBeforeMount(async () => {
  axios.defaults.headers.common['X-CSRFToken'] = Cookies.get("csrftoken");
  await fetchCategories();
  await fetchProducts();
});

</script>

<template>
<div class="container my-4">

    <form @submit.prevent.stop="onProductAdd">
    <div class="row">
        <div class="col">
        <div class="form-floating">
            
            <input
            type="text"
            class="form-control"
            v-model="productToAdd.name"
            required
            />
            <label for="floatingInput">Название</label>
        </div>
        </div>
        <div class="col-auto">
        <div class="form-floating">
            <select class="form-select" v-model="productToAdd.category" required>
            <option :value="c.id" v-for="c in categories">{{ c.name }}</option>
            </select>
            <label for="floatingInput">Группа</label>
        </div>
        </div>
        <div class="col-auto">
        <button class="btn btn-primary">
            Добавить
        </button>
        </div>
    </div>
    </form>

    <hr />

    <div v-for="item in products" :key="item.id" class="py-1">
      {{ item.name }} — {{ item.price }} руб.
    </div>
  </div>
</template>

<style scoped></style>
