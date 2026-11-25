<script setup>
import axios from 'axios';
import ColumnFilters from '@/components/ColumnFilters.vue';
import Pagination from '@/components/Pagination.vue';
import UserFilter from '@/components/UserFilter.vue';
import { onBeforeMount, ref, watch } from 'vue';

const statuses = {
  created: "Создан",
  in_progress: "В обработке",
  delivering: "В доставке",
  completed: "Завершен",
  cancelled: "Отменен"
};
const filterFields = [
  { name: 'id', label: 'Номер заказа', type: 'number' },
  { name: 'total_price', label: 'Сумма, ₽', type: 'number', step: '0.01' },
  { name: 'status', label: 'Статус', options: statuses },
  { name: 'client__username__icontains', label: 'Логин клиента' },
  { name: 'delivery_adress__icontains', label: 'Адрес' },
  { name: 'client__profile__phone__icontains', label: 'Телефон' },
  { name: 'comment__icontains', label: 'Комментарий' },
];
const filters = ref({});
const page = ref(1);
const total = ref(0);
const selectedUser = ref("");
const stats = ref(null);

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

async function fetchOrders(newPage = page.value) {
  page.value = newPage;
  const activeFilters = filters.value;
  const params = { ...activeFilters, user: selectedUser.value, page: newPage };
  const [list, summary] = await Promise.all([
    axios.get("/api/orders/", { params }),
    axios.get("/api/orders/stats/", { params }),
  ]);
  if (params.user !== selectedUser.value || newPage !== page.value || activeFilters !== filters.value) return;
  orders.value = list.data.results;
  total.value = list.data.count;
  stats.value = summary.data;
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
  await fetchOrders(Object.keys(filters.value).length ? 1 : page.value);
}

async function onRemoveClick(order) {
  await axios.delete(`/api/orders/${order.id}/`);
  if (orders.value.length === 1 && page.value > 1) page.value--;
  await fetchOrders();
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
watch([selectedUser, filters], () => fetchOrders(1));
</script>

<template>
  <div class="container my-4">
    <h2>Управление заказами</h2>
    <UserFilter v-model="selectedUser" />

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

    <ColumnFilters :fields="filterFields" @apply="filters = $event" />
    <div class="card shadow-sm">
      <div v-if="stats" class="card-header">
        Всего заказов: {{ stats.total }} · Завершено: {{ stats.completed }} ·
        Средняя сумма заказа: {{ stats.average_total === null ? '—' : Number(stats.average_total).toFixed(2) + ' ₽' }}
      </div>
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
            <span class="badge bg-info text-dark ms-2">{{ statuses[item.status] || item.status }}</span>
            <div class="text-muted small">
              Клиент: {{ getClientName(item.client) }}
            </div>
            <div class="text-muted small" v-if="item.delivery_adress">
              Адрес: {{ item.delivery_adress }}
            </div>
            <div class="text-muted small" v-if="item.client_phone">
              Телефон: {{ item.client_phone }}
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

    <Pagination :page="page" :total="total" @change="fetchOrders" />

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
