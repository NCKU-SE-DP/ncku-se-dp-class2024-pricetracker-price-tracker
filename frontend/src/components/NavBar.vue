<template>
    <nav class="navbar">
        <div class="title"> <RouterLink to="/overview">價格追蹤小幫手</RouterLink></div>
        <ul class="options">
            <li><RouterLink to="/overview">物價概覽</RouterLink></li>
            <li><RouterLink to="/trending">物價趨勢</RouterLink></li>
            <li><RouterLink to="/news">相關新聞</RouterLink></li>
            <li v-if="!isLoggedIn"><RouterLink to="/login">登入</RouterLink></li>
            <li v-else @click="logout">Hi, {{getUserName}}! 登出</li>
        </ul>
        <div class="menu-icon" @click="toggleMenu">☰</div>
    </nav>
    <div class="mobile-menu" :class="{ active: menuActive }">
        <RouterLink to="/overview">物價概覽</RouterLink>
        <RouterLink to="/trending">物價趨勢</RouterLink>
        <RouterLink to="/news">相關新聞</RouterLink>
        <RouterLink to="/login">登入</RouterLink>
    </div>
</template>

<script>
import { useAuthStore } from '@/stores/auth';

export default {
    name: 'NavBar',
    data() {
        return {
            menuActive: false
        };
    },
    computed: {
        isLoggedIn(){
            const userStore = useAuthStore();
            return userStore.isLoggedIn;
        },
        getUserName(){
            const userStore = useAuthStore();
            return userStore.getUserName;
        }
    },
    methods: {
        toggleMenu() {
            this.menuActive = !this.menuActive; 
        },
        logout(){
            const userStore = useAuthStore();
            userStore.logout();
        }
    }
};
</script>

<style scoped>
.navbar {
    display: flex;
    justify-content: space-between;
    background-color: #f3f3f3;
    padding: 1.5em;
    height: 4.5em;
    width: 100%;
    align-items: center;
    box-shadow: 0 0 5px #000000;
}

.navbar ul {
    list-style: none;
    display: flex;
    justify-content: space-around;
}

.title > a{
    font-size: 1.4em;
    font-weight: bold;
    color: #2c3e50 !important;
}

.navbar li {
    color: #575B5D;
    margin: 0 .5em;
    font-size: 1.2em;
}

.navbar li:hover{
    cursor: pointer;
    font-weight: bold;
}

.navbar a {
    text-decoration: none;
    color: #575B5D;
}

.mobile-menu {
    padding-top: 80px;
    display: none;
    flex-direction: column;
    width: 100%;
    background-color: #f4f4f4;
}

.navbar .menu-icon {
    display: none;
    font-size: 2rem;
    cursor: pointer;
}

.mobile-menu a {
    padding: 10px;
    text-decoration: none;
    color: black;
    display: block;
    text-align: center;
}

@media (max-width: 768px) {
    .navbar ul {
        display: none;
    }

    .navbar .menu-icon {
        display: block;
    }

    .mobile-menu.active {
        display: flex;
    }
}


</style>