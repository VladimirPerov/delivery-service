<script setup>
import useProfileStore from '@/stores/profileStore';
import { storeToRefs } from 'pinia';


const profileStore = useProfileStore();
const {
    isAuthenticated,
    userName
} = storeToRefs(profileStore)


async function onLogoutButtonClick() {
    profileStore.logout();
}
</script>

<template>
    <nav class="navbar navbar-expand-lg bg-body-tertiary mb-4">
        <div class="container-fluid">
            <router-link class="navbar-brand" to="/">Доставка</router-link>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
                aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse justify-content-between" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <router-link class="nav-link" to="/">Главная</router-link>
                    </li>
                    <li class="nav-item">
                        <router-link class="nav-link" to="/categories">Категории</router-link>
                    </li>
                    <li class="nav-item">
                        <router-link class="nav-link" to="/products">Продукты</router-link>
                    </li>
                    <li class="nav-item">
                        <router-link class="nav-link" to="/profiles">Профили</router-link>
                    </li>
                    <li class="nav-item">
                        <router-link class="nav-link" to="/orders">Заказы</router-link>
                    </li>
                    <li class="nav-item">
                        <router-link class="nav-link" to="/order-items">Позиции заказов</router-link>
                    </li>
                    <li class="nav-item">
                        <router-link class="nav-link" to="/deliveries">Доставки</router-link>
                    </li>
                    <li class="nav-item">
                        <router-link class="nav-link" to="/payments">Платежи</router-link>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link text-muted" href="/admin" target="_blank">Админка</a>
                    </li>
                </ul>

                <div class="d-flex align-items-center gap-3">
                    <template v-if="isAuthenticated">
                        <span class="navbar-text">Авторизован: <strong>{{ userName }}</strong></span>
                        <button class="btn btn-outline-danger btn-sm" @click="onLogoutButtonClick">
                            Выйти
                        </button>
                    </template>
                    <template v-else>
                        <router-link class="btn btn-outline-primary btn-sm" to="/login">Войти</router-link>
                    </template>
                </div>
            </div>
        </div>
    </nav>
</template>