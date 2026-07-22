<script setup lang="ts">
import Sidebar from './Sidebar.vue'
import HeaderBar from './HeaderBar.vue'
</script>

<template>
  <el-container class="layout">
    <el-aside width="210px" class="aside">
      <Sidebar />
    </el-aside>
    <el-container>
      <el-header height="56px" style="padding: 0">
        <HeaderBar />
      </el-header>
      <el-main class="main">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout {
  height: 100vh;
}
.aside {
  background: #1f2d3d;
  overflow: hidden;
}
.main {
  background: #f5f7fa;
  padding: 16px;
}
</style>
