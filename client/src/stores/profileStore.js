import { defineStore } from "pinia";
import {ref, onBeforeMount} from 'vue';
import axios from 'axios';
import Cookies from "js-cookie";

const useProfileStore = defineStore('profileStore', () => {

    const isAuthenticated = ref(false);
    const userName = ref(null);
    const isSuperuser = ref(false);
    
    async function fetchMe() {
        const r = await axios.get("/api/profile/me/");
        axios.defaults.headers.common['X-CSRFToken'] = Cookies.get("csrftoken");
        isAuthenticated.value = r.data.is_authenticated;
        userName.value = r.data.is_authenticated ? r.data.username : null;
        isSuperuser.value = r.data.is_authenticated ? r.data.is_superuser : false;
    }

    async function login(username, password) {
        const r = await axios.post('/api/profile/login/', {
            username: username,
            password: password,
        })
        fetchMe();
    }

    async function logout() {
        await axios.post("/api/profile/logout/")
        fetchMe();
    }

    onBeforeMount(() => {
        fetchMe();
    })

    return {
        isAuthenticated,
        userName,
        isSuperuser,

        fetchMe,
        login,
        logout,
    }
})

export default useProfileStore;
