<template>
  <div style="max-width:680px">
    <el-card>
      <template #header><b>灾情上报</b></template>
      <el-form :model="form" label-width="90px">
        <el-form-item label="灾情标题">
          <el-input v-model="form.title" placeholder="如：XX 镇山体滑坡" />
        </el-form-item>
        <el-form-item label="灾害类型">
          <el-select v-model="form.type" style="width:100%">
            <el-option label="地震" value="EARTHQUAKE" />
            <el-option label="洪涝" value="FLOOD" />
            <el-option label="滑坡" value="LANDSLIDE" />
          </el-select>
        </el-form-item>
        <el-form-item label="等级">
          <el-input v-model="form.level" placeholder="如 Ⅱ级 / 重大" />
        </el-form-item>
        <el-form-item label="地点描述">
          <el-input v-model="form.locationText" placeholder="如：XX 县 XX 镇 XX 村" />
        </el-form-item>
        <el-form-item label="灾情描述">
          <el-input type="textarea" v-model="form.content" :rows="5" placeholder="描述受灾范围、人员、房屋、道路等情况" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="form.contact" placeholder="上报人电话" />
        </el-form-item>
        <el-button type="primary" @click="submit">提交上报</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { submitReport } from '../api'

const router = useRouter()
const form = ref<any>({
  title: '', type: 'EARTHQUAKE', level: '', locationText: '', content: '', contact: ''
})

async function submit() {
  if (!form.value.content) { ElMessage.warning('请填写灾情描述'); return }
  await submitReport(form.value)
  ElMessage.success('已上报，等待核验')
  router.push('/')
}
</script>
