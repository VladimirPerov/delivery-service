import { createRouter, createWebHistory } from 'vue-router'

import LoginPage from '@/pages/LoginPage.vue'
import MainPage from '@/pages/MainPage.vue'

import CategoryPage from '@/pages/CategoryPage.vue'
import ProductPage from '@/pages/ProductPage.vue'
import ProfilePage from '@/pages/ProfilePage.vue'
import OrderPage from '@/pages/OrderPage.vue'
import OrderItemPage from '@/pages/OrderItemPage.vue'
import DeliveryPage from '@/pages/DeliveryPage.vue'
import PaymentPage from '@/pages/PaymentPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      component: MainPage
    },
    {
      path: "/login",
      component: LoginPage
    },
    { 
      path: '/categories', 
      component: CategoryPage 
    },
    { 
      path: '/products', 
      component: ProductPage 
    },
    { 
      path: '/profiles', 
      component: ProfilePage 
    },
    { 
      path: '/orders', 
      component: OrderPage 
    },
    { 
      path: '/order-items', 
      component: OrderItemPage 
    },
    { 
      path: '/deliveries', 
      component: DeliveryPage 
    },
    { 
      path: '/payments', 
      component: PaymentPage 
    },
  ],
})

export default router
