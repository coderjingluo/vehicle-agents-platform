<template>
  <div class="not-found">
    <h1>404</h1>
    <p>页面不存在</p>
    <el-button type="primary" @click="goHome">返回首页</el-button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

const goHome = () => {
  router.push('/');
};
</script>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background-color: #111215;
  color: #fff;
}

h1 {
  font-size: 120px;
  margin-bottom: 20px;
  color: #4080ff;
}

p {
  font-size: 24px;
  margin-bottom: 30px;
}
</style> 