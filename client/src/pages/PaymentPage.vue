<script setup>
import axios from 'axios';
import { onBeforeMount, ref } from 'vue';

const payments = ref([]);
const orders = ref([]);

const paymentToAdd = ref({
  order: null,
  payment_method: 'card',
  amount: '0.00',
  status: 'pending'
});

const paymentToEdit = ref({});

async function fetchPayments() {
    const r = await axios.get("/api/payments/");
    payments.value = r.data;
}

async function fetchOrders() {
  const r = await axios.get("/api/orders/");
  orders.value = r.data;
}

async function onPaymentAdd() {
  await axios.post("/api/payments/", paymentToAdd.value);
  paymentToAdd.value = {
    order: null,
    payment_method: 'card',
    amount: '0.00',
    status: 'pending'
  };
  await fetchPayments();
}

function onPaymentEditClick(payment) {
  paymentToEdit.value = { ...payment };
}

async function onUpdatePayment() {
  await axios.put(`/api/payments/${paymentToEdit.value.id}/`, paymentToEdit.value);
  await fetchPayments();
}

async function onRemoveClick(payment) {
  await axios.delete(`/api/payments/${payment.id}/`);
  await fetchPayments();
}

function getMethodLabel(method) {
  const map = {
    cash: "Наличные",
    card: "Банковская карта",
    sbp: "Система быстрых платежей"
  };
  return map[method] || method;
}

function getStatusLabel(status) {
  const map = {
    pending: "Ожидает оплаты",
    paid: "Оплачен",
    failed: "Ошибка оплаты",
    refunded: "Возвращен"
  };
  return map[status] || status;
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? dateStr : d.toLocaleString();
}

onBeforeMount(async () => {
  await Promise.all([
    fetchPayments(),
    fetchOrders()
  ]);
});
</script>

<template>
  <div class="container my-4">
    <h2>Управление платежами</h2>

    <form @submit.prevent.stop="onPaymentAdd" class="card p-3 mb-4 shadow-sm">
      <h5 class="mb-3">Добавить новый платеж</h5>
      <div class="row g-3">
        <div class="col-md-6">
          <div class="form-floating">
            <select class="form-select" v-model="paymentToAdd.order" required id="newOrder">
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
            <input 
              type="number" 
              step="0.01" 
              class="form-control" 
              v-model="paymentToAdd.amount" 
              required 
              id="newAmount" 
              placeholder="Сумма" 
            />
            <label for="newAmount">Сумма платежа</label>
          </div>
        </div>

        <div class="col-md-6">
          <div class="form-floating">
            <select class="form-select" v-model="paymentToAdd.payment_method" id="newMethod">
              <option value="card">Банковская карта</option>
              <option value="cash">Наличные</option>
              <option value="sbp">Система быстрых платежей</option>
            </select>
            <label for="newMethod">Способ оплаты</label>
          </div>
        </div>

        <div class="col-md-6">
          <div class="form-floating">
            <select class="form-select" v-model="paymentToAdd.status" id="newStatus">
              <option value="pending">Ожидает оплаты</option>
              <option value="paid">Оплачен</option>
              <option value="failed">Ошибка оплаты</option>
              <option value="refunded">Возвращен</option>
            </select>
            <label for="newStatus">Статус оплаты</label>
          </div>
        </div>

        <div class="col-12">
          <button class="btn btn-primary w-100">Добавить платеж</button>
        </div>
      </div>
    </form>

    <div class="card shadow-sm">
      <div class="card-body">
        <div v-if="payments.length === 0" class="text-center text-muted py-3">
          Платежи не найдены.
        </div>
        <div 
          v-for="item in payments" 
          :key="item.id" 
          class="d-flex justify-content-between align-items-center border-bottom py-2"
        >
          <div>
            <strong>Платеж #{{ item.id }}</strong> (Заказ #{{ item.order }}) — 
            <strong>{{ item.amount }} руб.</strong>
            <span class="badge bg-secondary ms-2">{{ getMethodLabel(item.payment_method) }}</span>
            <span class="badge bg-info text-dark ms-2">{{ getStatusLabel(item.status) }}</span>
            <div class="text-muted small" v-if="item.payment_date">
              Дата оплаты: {{ formatDate(item.payment_date) }}
            </div>
          </div>
          <div class="btn-group">
            <button
              class="btn btn-outline-success btn-sm"
              @click="onPaymentEditClick(item)"
              data-bs-toggle="modal"
              data-bs-target="#editPaymentModal">
              Изменить
            </button>
            <button class="btn btn-outline-danger btn-sm" @click="onRemoveClick(item)">
              Удалить
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="modal fade" id="editPaymentModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h1 class="modal-title fs-5">Редактировать платеж</h1>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <div class="form-floating">
                <select class="form-select" v-model="paymentToEdit.order" id="editOrder">
                  <option :value="o.id" v-for="o in orders" :key="o.id">
                    Заказ #{{ o.id }}
                  </option>
                </select>
                <label for="editOrder">Заказ</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <input 
                  type="number" 
                  step="0.01" 
                  class="form-control" 
                  v-model="paymentToEdit.amount" 
                  id="editAmount" 
                  placeholder="Сумма" 
                />
                <label for="editAmount">Сумма платежа</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <select class="form-select" v-model="paymentToEdit.payment_method" id="editMethod">
                  <option value="card">Банковская карта</option>
                  <option value="cash">Наличные</option>
                  <option value="sbp">Система быстрых платежей</option>
                </select>
                <label for="editMethod">Способ оплаты</label>
              </div>
            </div>

            <div class="mb-3">
              <div class="form-floating">
                <select class="form-select" v-model="paymentToEdit.status" id="editStatus">
                  <option value="pending">Ожидает оплаты</option>
                  <option value="paid">Оплачен</option>
                  <option value="failed">Ошибка оплаты</option>
                  <option value="refunded">Возвращен</option>
                </select>
                <label for="editStatus">Статус оплаты</label>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
            <button data-bs-dismiss="modal" type="button" class="btn btn-primary" @click="onUpdatePayment">
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