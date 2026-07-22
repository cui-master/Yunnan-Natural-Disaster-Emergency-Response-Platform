<template>
  <div>
    <div style="margin-bottom:16px">
      <el-button type="primary" @click="showAdd = true">新增资源</el-button>
    </div>
    <el-table :data="resources" stripe>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="type" label="类型" width="100" />
      <el-table-column prop="total" label="总量" width="90" />
      <el-table-column prop="available" label="可用" width="90" />
      <el-table-column prop="unit" label="单位" width="80" />
      <el-table-column prop="status" label="状态" width="100" />
    </el-table>

    <el-dialog v-model="showAdd" title="新增资源">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.type" style="width:100%">
            <el-option label="人员" value="PERSONNEL" />
            <el-option label="车辆" value="VEHICLE" />
            <el-option label="物资" value="MATERIAL" />
            <el-option label="避难所" value="SHELTER" />
          </el-select>
        </el-form-item>
        <el-form-item label="总量"><el-input-number v-model="form.total" /></el-form-item>
        <el-form-item label="可用"><el-input-number v-model="form.available" /></el-form-item>
        <el-form-item label="单位"><el-input v-model="form.unit" /></el-form-item>
      </el-form>
      <el-button type="primary" @click="add">保存</el-button>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listResources, createResource } from '../api'
import { ElMessage } from 'element-plus'
import type { Resource } from '../types'

const resources = ref<Resource[]>([])
const showAdd = ref(false)
const form = ref<any>({ name: '', type: 'PERSONNEL', total: 0, available: 0, unit: '' })

async function load() { resources.value = await listResources() }
async function add() {
  await createResource(form.value)
  ElMessage.success('已新增')
  showAdd.value = false
  load()
}
onMounted(load)
</script>
