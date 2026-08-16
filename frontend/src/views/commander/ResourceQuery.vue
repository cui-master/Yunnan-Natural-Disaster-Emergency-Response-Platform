<template>
  <div class="resource-query-page">
    <div class="page-header">
      <div class="header-title">
        <el-icon :size="22" color="#52c41a"><Search /></el-icon>
        <span>救援资源查询</span>
      </div>
    </div>

    <div class="query-bar">
      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="资源类型">
          <el-select v-model="queryForm.type" style="width: 160px;">
            <el-option label="仓库" value="warehouse" />
            <el-option label="救援队伍" value="team" />
            <el-option label="避难场所" value="shelter" />
            <el-option label="物资品类" value="material" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" clearable style="width: 140px;">
            <el-option label="正常/空闲/可用" value="正常" />
            <el-option label="已调度" value="已调度" />
            <el-option label="维修中" value="维修中" />
          </el-select>
        </el-form-item>
        <el-form-item label="所在州市">
          <el-select v-model="queryForm.city" clearable style="width: 140px;">
            <el-option v-for="c in cities" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称/单位">
          <el-input v-model="queryForm.keyword" placeholder="搜索关键词" style="width: 180px;" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="result-card">
      <div class="result-header">
        <span>共找到 <b style="color: #e64545;">{{ total }}</b> 条结果</span>
        <el-button type="primary" :icon="Plus" size="small">新增资源</el-button>
      </div>

      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column v-if="queryForm.type === 'warehouse'" prop="name" label="仓库名称" min-width="200" />
        <el-table-column v-if="queryForm.type === 'warehouse'" prop="type" label="类型" width="100" />
        <el-table-column v-if="queryForm.type === 'warehouse'" prop="city" label="所在州市" width="120" />
        <el-table-column v-if="queryForm.type === 'warehouse'" prop="capacity" label="容量" width="100" />
        <el-table-column v-if="queryForm.type === 'warehouse'" prop="manager" label="负责人" width="100" />
        <el-table-column v-if="queryForm.type === 'warehouse'" prop="contact" label="联系方式" width="140" />

        <el-table-column v-if="queryForm.type === 'team'" prop="name" label="队伍名称" min-width="200" />
        <el-table-column v-if="queryForm.type === 'team'" prop="type" label="类型" width="120" />
        <el-table-column v-if="queryForm.type === 'team'" prop="city" label="所在州市" width="120" />
        <el-table-column v-if="queryForm.type === 'team'" prop="members" label="人数" width="100" />
        <el-table-column v-if="queryForm.type === 'team'" prop="carryLimit" label="装备类型" width="120" />
        <el-table-column v-if="queryForm.type === 'team'" prop="manager" label="队长" width="100" />

        <el-table-column v-if="queryForm.type === 'shelter'" prop="name" label="场所名称" min-width="200" />
        <el-table-column v-if="queryForm.type === 'shelter'" prop="type" label="类型" width="120" />
        <el-table-column v-if="queryForm.type === 'shelter'" prop="city" label="所在州市" width="120" />
        <el-table-column v-if="queryForm.type === 'shelter'" label="容量/已容纳" width="160">
          <template #default="{ row }">
            {{ row.accommodated }} / {{ row.capacity }}
          </template>
        </el-table-column>
        <el-table-column v-if="queryForm.type === 'shelter'" prop="address" label="地址" min-width="180" />

        <el-table-column v-if="queryForm.type === 'material'" prop="name" label="物资名称" min-width="180" />
        <el-table-column v-if="queryForm.type === 'material'" prop="type" label="品类" width="120" />
        <el-table-column v-if="queryForm.type === 'material'" prop="unit" label="单位" width="80" />
        <el-table-column v-if="queryForm.type === 'material'" prop="weight" label="重量(kg)" width="100" />
        <el-table-column v-if="queryForm.type === 'material'" prop="suitable" label="适用灾害" min-width="180" />

        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small" effect="light">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="160" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" link>详情</el-button>
            <el-button size="small" type="primary" link>调度</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getResourceList } from '@/api'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'

const cities = ['昆明市', '曲靖市', '玉溪市', '保山市', '昭通市', '丽江市', '普洱市', '临沧市', '楚雄州', '红河州', '文山州', '西双版纳', '大理州', '德宏州', '怒江州', '迪庆州']

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

const queryForm = reactive({
  type: 'warehouse',
  status: '',
  city: '',
  keyword: ''
})

function statusTagType(status) {
  const map = {
    '正常': 'success',
    '空闲': 'success',
    '可用': 'success',
    '已调度': 'warning',
    '训练中': 'info',
    '维修中': 'danger',
    '禁用': 'danger'
  }
  return map[status] || 'info'
}

async function loadData() {
  loading.value = true
  try {
    const res = await getResourceList({ type: queryForm.type, status: queryForm.status })
    if (res.success) {
      tableData.value = res.data.list
      total.value = res.data.total
    }
  } finally {
    loading.value = false
  }
}

function handleReset() {
  queryForm.status = ''
  queryForm.city = ''
  queryForm.keyword = ''
  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.resource-query-page {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}

.page-header {
  margin-bottom: 16px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.query-bar {
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.query-form {
  margin: 0;
}

.result-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  font-size: 14px;
  color: #6b7280;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .query-bar {
    padding: 12px;
  }

  .query-form :deep(.el-form-item) {
    margin-right: 0;
    width: 100%;
  }
}
</style>
