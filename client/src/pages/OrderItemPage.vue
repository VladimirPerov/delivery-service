<script setup>
import axios from 'axios';
import UserFilter from '@/components/UserFilter.vue';
import { onBeforeMount, ref, watch } from 'vue';

const selectedUser = ref("");

const orderItems = ref([]);
const products = ref([]);
const orders = ref([]);

const orderItemToAdd = ref({
  product: null,
  order: null,
  quantity: 1,
  price_at_time: '0.00'
});

const orderItemToEdit = ref({});

async function fetchOrderItems() {
  const r = await axios.get("/api/order-items/", { params: { user: selectedUser.value } });
  orderItems.value = r.data;
}

async function fetchProducts() {
  const r = await axios.get("/api/products/");
  products.value = r.data;
}

async function fetchOrders() {
  const r = await axios.get("/api/orders/");
  orders.value = r.data;
}

async function onOrderItemAdd() {
  await axios.post("/api/order-items/", orderItemToAdd.value);
  orderItemToAdd.value = {
    product: null,
    order: null,
    quantity: 1,
    price_at_time: '0.00'
  };
  await fetchOrderItems();
}

function onOrderItemEditClick(item) {
  orderItemToEdit.value = { ...item };
}

async function onUpdateOrderItem() {
  await axios.put(`/api/order-items/${orderItemToEdit.value.id}/`, orderItemToEdit.value);
  await fetchOrderItems();
}

async function onRemoveClick(item) {
  await axios.delete(`/api/order-items/${item.id}/`);
  await fetchOrderItems();
}

function getProductName(productId) {
  const product = products.value.find(p => p.id === productId);
  return product ? product.name : `Продукт #${productId}`;
}

onBeforeMount(async () => {
  await Promise.all([
    fetchOrderItems(),
    fetchProducts(),
    fetchOrders()
  ]);
});
watch(selectedUser, fetchOrderItems);
</script>

<template>
  <div class="container my-4">
    <h2>Управление позициями заказа</h2>
    <UserFilter v-model="selectedUser" />

    <form @submit.prevent.stop="onOrderItemAdd" class="card p-3 mb-4 shadow-sm">
      <h5 class="mb-3">Добавить позицию заказа</h5>
      <div class="row g-3">
        <div class="col-md-6">
          <div class="form-floating">
            <select class="form-select" v-model="orderItemToAdd.order" required id="newOrder">
              <option :value="null" disabled>Выберите заказ</option>
              <option :value="o.id" v-for="o in orders" :key="o.id">
                Заказ #{{ o.id }}
              </option>
            </select>
            <label for="newOrder">Заказ</label>
          </div>
        </div>

        <div class="col-md-6">
          <div class="form-floating">
            <select class="form-select" v-model="orderItemToAdd.product" required id="newProduct">
              <option :value="null" disabled>Выберите продукт</option>
              <option :value="p.id" v-for="p in products" :key="p.id">
                {{ p.name }}
              </option>
            </select>
            <label for="newProduct">Продукт</label>
          </div>
        </div>

        <div class="col-md-6">
          <div class="form-floating">
            <input 
              type="number" 
              class="form-control" 
              v-model="orderItemToAdd.quantity" 
              required 
              id="newQuantity" 
              placeholder="Количество" 
            />
            <label for="newQuantity">Количество в заказе</label>
          </div>
        </div>

        <div class="col-md-6">
          <div class="form-floating">
            <input 
              type="number" 
              step="0.01" 
              class="form-control" 
              v-model="orderItemToAdd.price_at_time" 
              required 
              id="newPrice" 
              placeholder="Цена" 
            />
            <label for="newPrice">Цена в момент заказа</label>
          </div>
        </div>

        <div class="col-12">
          <button class="btn btn-primary w-100">Добавить позицию</button>
        </div>
      </div>
    </form>

    <div class="card shadow-sm">
      <div class="card-body">
        <div v-if="orderItems.length === 0" class="text-center text-muted py-3">
          Позиции заказа не найдены.
        </div>
        <div 
          v-for="item in orderItems" 
          :key="item.id" 
          class="d-flex justify-content-between align-items-center border-bottom py-2"
        >
          <div>
            <strong>{{ getProductName(item.product) }}</strong> — 
            <span>{{ item.quantity }} шт.</span> по 
            <strong>{{ item.price_at_time }} руб.</strong>
            <div class="text-muted small" v-if="item.order">
              Заказ #{{ item.order }}
            </div>
          </div>
          <div class="btn-group">
            <button
              class="btn btn-outline-success btn-sm"
              @click="onOrderItemEditClick(item)"
              data-bs-toggle="modal"
              data-bs-target="#editOrderItemModal">
              Изменить
            </button>
            <button class="btn btn-outline-danger btn-sm" @click="onRemoveClick(item)">
              Удалить
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="modal fade" id="editOrderItemModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title fs-5">Редактировать позицию заказа</h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <div class="form-floating">
                <select class="form-select" v-model="orderItemToEdit.order" id="editOrder">
                  <option :value="o.id" v-for="o in orders" :key="o.id">
                    Заказ #{{ o.id }}
                  </option>
                </select>
                <label for="editOrder">Заказ</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <select class="form-select" v-model="orderItemToEdit.product" id="editProduct">
                  <option :value="p.id" v-for="p in products" :key="p.id">
                    {{ p.name }}
                  </option>
                </select>
                <label for="editProduct">Продукт</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <input 
                  type="number" 
                  class="form-control" 
                  v-model="orderItemToEdit.quantity" 
                  id="editQuantity" 
                  placeholder="Количество" 
                />
                <label for="editQuantity">Количество в заказе</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <input 
                  type="number" 
                  step="0.01" 
                  class="form-control" 
                  v-model="orderItemToEdit.price_at_time" 
                  id="editPrice" 
                  placeholder="Цена" 
                />
                <label for="editPrice">Цена в момент заказа</label>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
            <button data-bs-dismiss="modal" type="button" class="btn btn-primary" @click="onUpdateOrderItem">
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