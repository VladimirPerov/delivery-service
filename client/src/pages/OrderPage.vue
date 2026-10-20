<script setup>
import axios from 'axios';
import { onBeforeMount, ref } from 'vue';

const orders = ref([]);
const users = ref([]);

const orderToAdd = ref({
  client: null,
  total_price: '0.00',
  status: 'created',
  delivery_adress: '',
  comment: ''
});

const orderToEdit = ref({});

async function fetchOrders() {
  const r = await axios.get("/api/orders/");
  orders.value = r.data;
}

async function fetchUsers() {
  const r = await axios.get("/api/users/");
  users.value = r.data;
}

async function onOrderAdd() {
  await axios.post("/api/orders/", orderToAdd.value);
  orderToAdd.value = {
    client: null,
    total_price: '0.00',
    status: 'created',
    delivery_adress: '',
    comment: ''
  };
  await fetchOrders();
}

function onOrderEditClick(order) {
  orderToEdit.value = { ...order };
}

async function onUpdateOrder() {
  await axios.put(`/api/orders/${orderToEdit.value.id}/`, orderToEdit.value);
  await fetchOrders();
}

async function onRemoveClick(order) {
  await axios.delete(`/api/orders/${order.id}/`);
  await fetchOrders();
}

function getStatusLabel(status) {
  const map = {
    created: "Создан",
    in_progress: "В обработке",
    delivering: "В доставке",
    completed: "Завершен",
    cancelled: "Отменен"
  };
  return map[status] || status;
}

function getClientName(clientId) {
  const user = users.value.find(u => u.id === clientId);
  if (!user) return "Клиент не указан";
  return user.username || user.first_name || `Пользователь #${user.id}`;
}

onBeforeMount(async () => {
  await Promise.all([
    fetchOrders(),
    fetchUsers()
  ]);
});
</script>

<template>
  <div class="container my-4">
    <h2>Управление заказами</h2>

    <form @submit.prevent.stop="onOrderAdd" class="card p-3 mb-4 shadow-sm">
      <h5 class="mb-3">Добавить новый заказ</h5>
      <div class="row g-3">
        <div class="col-md-6">
          <div class="form-floating">
            <select class="form-select" v-model="orderToAdd.client" id="newClient">
              <option :value="null">Без клиента</option>
              <option :value="u.id" v-for="u in users" :key="u.id">
                {{ u.username || u.first_name || `Пользователь #${u.id}` }}
              </option>
            </select>
            <label for="newClient">Клиент</label>
          </div>
        </div>

        <div class="col-md-3">
          <div class="form-floating">
            <input 
              type="number" 
              step="0.01" 
              class="form-control" 
              v-model="orderToAdd.total_price" 
              id="newTotalPrice" 
              placeholder="Цена" 
            />
            <label for="newTotalPrice">Итоговая цена</label>
          </div>
        </div>

        <div class="col-md-3">
          <div class="form-floating">
            <select class="form-select" v-model="orderToAdd.status" id="newStatus">
              <option value="created">Создан</option>
              <option value="in_progress">В обработке</option>
              <option value="delivering">В доставке</option>
              <option value="completed">Завершен</option>
              <option value="cancelled">Отменен</option>
            </select>
            <label for="newStatus">Статус заказа</label>
          </div>
        </div>

        <div class="col-12">
          <div class="form-floating">
            <input 
              type="text" 
              class="form-control" 
              v-model="orderToAdd.delivery_adress" 
              id="newDeliveryAddress" 
              placeholder="Адрес" 
            />
            <label for="newDeliveryAddress">Адрес доставки</label>
          </div>
        </div>

        <div class="col-12">
          <div class="form-floating">
            <textarea 
              class="form-control" 
              v-model="orderToAdd.comment" 
              id="newComment" 
              style="height: 80px" 
              placeholder="Комментарий"
            ></textarea>
            <label for="newComment">Комментарий</label>
          </div>
        </div>

        <div class="col-12">
          <button class="btn btn-primary w-100">Добавить заказ</button>
        </div>
      </div>
    </form>

    <div class="card shadow-sm">
      <div class="card-body">
        <div v-if="orders.length === 0" class="text-center text-muted py-3">
          Заказы не найдены.
        </div>
        <div 
          v-for="item in orders" 
          :key="item.id" 
          class="d-flex justify-content-between align-items-center border-bottom py-2"
        >
          <div>
            <strong>Заказ #{{ item.id }}</strong> — <strong>{{ item.total_price }} руб.</strong>
            <span class="badge bg-info text-dark ms-2">{{ getStatusLabel(item.status) }}</span>
            <div class="text-muted small">
              Клиент: {{ getClientName(item.client) }}
            </div>
            <div class="text-muted small" v-if="item.delivery_adress">
              Адрес: {{ item.delivery_adress }}
            </div>
            <div class="text-muted small" v-if="item.comment">
              Комментарий: {{ item.comment }}
            </div>
          </div>
          <div class="btn-group">
            <button
              class="btn btn-outline-success btn-sm"
              @click="onOrderEditClick(item)"
              data-bs-toggle="modal"
              data-bs-target="#editOrderModal">
              Изменить
            </button>
            <button class="btn btn-outline-danger btn-sm" @click="onRemoveClick(item)">
              Удалить
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="modal fade" id="editOrderModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title fs-5">Редактировать заказ</h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <div class="form-floating">
                <select class="form-select" v-model="orderToEdit.client" id="editClient">
                  <option :value="null">Без клиента</option>
                  <option :value="u.id" v-for="u in users" :key="u.id">
                    {{ u.username || u.first_name || `Пользователь #${u.id}` }}
                  </option>
                </select>
                <label for="editClient">Клиент</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <input 
                  type="number" 
                  step="0.01" 
                  class="form-control" 
                  v-model="orderToEdit.total_price" 
                  id="editTotalPrice" 
                  placeholder="Цена" 
                />
                <label for="editTotalPrice">Итоговая цена</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <select class="form-select" v-model="orderToEdit.status" id="editStatus">
                  <option value="created">Создан</option>
                  <option value="in_progress">В обработке</option>
                  <option value="delivering">В доставке</option>
                  <option value="completed">Завершен</option>
                  <option value="cancelled">Отменен</option>
                </select>
                <label for="editStatus">Статус заказа</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="orderToEdit.delivery_adress" 
                  id="editDeliveryAddress" 
                  placeholder="Адрес" 
                />
                <label for="editDeliveryAddress">Адрес доставки</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <textarea 
                  class="form-control" 
                  v-model="orderToEdit.comment" 
                  id="editComment" 
                  style="height: 80px" 
                  placeholder="Комментарий"
                ></textarea>
                <label for="editComment">Комментарий</label>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
            <button data-bs-dismiss="modal" type="button" class="btn btn-primary" @click="onUpdateOrder">
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