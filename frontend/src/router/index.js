import { createWebHistory, createRouter } from 'vue-router';
import PriceOverview from '@/pages/PriceOverview.vue';
import PriceTrending from '@/pages/PriceTrending.vue';
import NewsList from '@/pages/NewsList.vue';
import UserLogin from '@/pages/UserLogin.vue';
import UserRegister from '@/pages/UserRegister.vue';

const routes = [
  {
    path: '/',
    redirect: '/overview'
  },
  {
    path: '/overview',
    name: 'PriceOverview',
    component: PriceOverview
  },
  {
    path: '/trending',
    name: 'PriceTrending',
    component: PriceTrending
  },
  {
    path: '/news',
    name: 'NewsList',
    component: NewsList
  },
  {
    path: '/login',
    name: 'UserLogin',
    component: UserLogin
  },
  {
    path: '/register',
    name: 'UserRegister',
    component: UserRegister
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/overview'
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
