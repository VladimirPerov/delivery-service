<script setup>
import axios from 'axios';
import UserFilter from '@/components/UserFilter.vue';
import { onBeforeMount, ref, watch } from 'vue';

const selectedUser = ref("");

const deliveries = ref([]);
const orders = ref([]);
const couriers = ref([]);

const deliveryToAdd = ref({
  order: null,
  courier: null,
  delivery_status: 'assigned',
  assigned_at: null,
  arrival_time: null
});

const deliveryToEdit = ref({});

function formatDateForInput(datetimeStr) {
  if (!datetimeStr) return '';
  const date = new Date(datetimeStr);
  if (isNaN(date.getTime())) return datetimeStr;
  const pad = (n) => (n < 10 ? '0' + n : n);
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

async function fetchDeliveries() {
  const r = await axios.get("/api/deliveries/", { params: { user: selectedUser.value } });
  deliveries.value = r.data;
}

async function fetchOrders() {
  const r = await axios.get("/api/orders/");
  orders.value = r.data;
}

async function fetchCouriers() {
  const r = await axios.get("/api/users/");
  couriers.value = r.data;
}

async function onDeliveryAdd() {
  const payload = {
    ...deliveryToAdd.value,
    assigned_at: deliveryToAdd.value.assigned_at ? new Date(deliveryToAdd.value.assigned_at).toISOString() : null,
    arrival_time: deliveryToAdd.value.arrival_time ? new Date(deliveryToAdd.value.arrival_time).toISOString() : null
  };
  await axios.post("/api/deliveries/", payload);
  deliveryToAdd.value = {
    order: null,
    courier: null,
    delivery_status: 'assigned',
    assigned_at: null,
    arrival_time: null
  };
  await fetchDeliveries();
}

function onDeliveryEditClick(delivery) {
  deliveryToEdit.value = {
    ...delivery,
    assigned_at: formatDateForInput(delivery.assigned_at),
    arrival_time: formatDateForInput(delivery.arrival_time)
  };
}

async function onUpdateDelivery() {
  const payload = {
    ...deliveryToEdit.value,
    assigned_at: deliveryToEdit.value.assigned_at ? new Date(deliveryToEdit.value.assigned_at).toISOString() : null,
    arrival_time: deliveryToEdit.value.arrival_time ? new Date(deliveryToEdit.value.arrival_time).toISOString() : null
  };
  await axios.put(`/api/deliveries/${deliveryToEdit.value.id}/`, payload);
  await fetchDeliveries();
}

async function onRemoveClick(delivery) {
  await axios.delete(`/api/deliveries/${delivery.id}/`);
  await fetchDeliveries();
}

function getStatusLabel(status) {
  const map = {
    assigned: "Назначена",
    in_transit: "В пути",
    delivered: "Доставлена",
    failed: "Ошибка доставки"
  };
  return map[status] || status;
}

function getCourierName(courierId) {
  const courier = couriers.value.find(c => c.id === courierId);
  if (!courier) return "Не назначен";
  return courier.username || courier.first_name || `Курьер #${courier.id}`;
}

onBeforeMount(async () => {
  await Promise.all([
    fetchDeliveries(),
    fetchOrders(),
    fetchCouriers()
  ]);
});
watch(selectedUser, fetchDeliveries);
</script>

<template>
  <div class="container my-4">
    <h2>Управление доставками</h2>
    <UserFilter v-model="selectedUser" />

    <form @submit.prevent.stop="onDeliveryAdd" class="card p-3 mb-4 shadow-sm">
      <h5 class="mb-3">Добавить новую доставку</h5>
      <div class="row g-3">
        <div class="col-md-6">
          <div class="form-floating">
            <select class="form-select" v-model="deliveryToAdd.order" id="newOrder">
              <option :value="null">Без заказа</option>
              <option :value="o.id" v-for="o in orders" :key="o.id">
                Заказ #{{ o.id }}
              </option>
            </select>
            <label for="newOrder">Заказ</label>
          </div>
        </div>

        <div class="col-md-6">
          <div class="form-floating">
            <select class="form-select" v-model="deliveryToAdd.courier" id="newCourier">
              <option :value="null">Не назначен</option>
              <option :value="c.id" v-for="c in couriers" :key="c.id">
                {{ c.username || c.first_name || `Пользователь #${c.id}` }}
              </option>
            </select>
            <label for="newCourier">Курьер</label>
          </div>
        </div>

        <div class="col-md-4">
          <div class="form-floating">
            <select class="form-select" v-model="deliveryToAdd.delivery_status" id="newStatus">
              <option value="assigned">Назначена</option>
              <option value="in_transit">В пути</option>
              <option value="delivered">Доставлена</option>
              <option value="failed">Ошибка доставки</option>
            </select>
            <label for="newStatus">Статус доставки</label>
          </div>
        </div>

        <div class="col-md-4">
          <div class="form-floating">
            <input 
              type="datetime-local" 
              class="form-control" 
              v-model="deliveryToAdd.assigned_at" 
              id="newAssignedAt" 
            />
            <label for="newAssignedAt">Время назначения</label>
          </div>
        </div>

        <div class="col-md-4">
          <div class="form-floating">
            <input 
              type="datetime-local" 
              class="form-control" 
              v-model="deliveryToAdd.arrival_time" 
              id="newArrivalTime" 
            />
            <label for="newArrivalTime">Время вручения</label>
          </div>
        </div>

        <div class="col-12">
          <button class="btn btn-primary w-100">Добавить доставку</button>
        </div>
      </div>
    </form>

    <div class="card shadow-sm">
      <div class="card-body">
        <div v-if="deliveries.length === 0" class="text-center text-muted py-3">
          Доставки не найдены.
        </div>
        <div 
          v-for="item in deliveries" 
          :key="item.id" 
          class="d-flex justify-content-between align-items-center border-bottom py-2"
        >
          <div>
            <strong>Доставка #{{ item.id }}</strong> 
            <span v-if="item.order"> (Заказ #{{ item.order }})</span> — 
            <span class="badge bg-info text-dark">{{ getStatusLabel(item.delivery_status) }}</span>
            <div class="text-muted small">
              Курьер: {{ getCourierName(item.courier) }}
            </div>
          </div>
          <div class="btn-group">
            <button
              class="btn btn-outline-success btn-sm"
              @click="onDeliveryEditClick(item)"
              data-bs-toggle="modal"
              data-bs-target="#editDeliveryModal">
              Изменить
            </button>
            <button class="btn btn-outline-danger btn-sm" @click="onRemoveClick(item)">
              Удалить
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="modal fade" id="editDeliveryModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title fs-5">Редактировать доставку</h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <div class="form-floating">
                <select class="form-select" v-model="deliveryToEdit.order" id="editOrder">
                  <option :value="null">Без заказа</option>
                  <option :value="o.id" v-for="o in orders" :key="o.id">
                    Заказ #{{ o.id }}
                  </option>
                </select>
                <label for="editOrder">Заказ</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <select class="form-select" v-model="deliveryToEdit.courier" id="editCourier">
                  <option :value="null">Не назначен</option>
                  <option :value="c.id" v-for="c in couriers" :key="c.id">
                    {{ c.username || c.first_name || `Пользователь #${c.id}` }}
                  </option>
                </select>
                <label for="editCourier">Курьер</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <select class="form-select" v-model="deliveryToEdit.delivery_status" id="editStatus">
                  <option value="assigned">Назначена</option>
                  <option value="in_transit">В пути</option>
                  <option value="delivered">Доставлена</option>
                  <option value="failed">Ошибка доставки</option>
                </select>
                <label for="editStatus">Статус доставки</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <input 
                  type="datetime-local" 
                  class="form-control" 
                  v-model="deliveryToEdit.assigned_at" 
                  id="editAssignedAt" 
                />
                <label for="editAssignedAt">Время назначения</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <input 
                  type="datetime-local" 
                  class="form-control" 
                  v-model="deliveryToEdit.arrival_time" 
                  id="editArrivalTime" 
                />
                <label for="editArrivalTime">Время вручения</label>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
            <button data-bs-dismiss="modal" type="button" class="btn btn-primary" @click="onUpdateDelivery">
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