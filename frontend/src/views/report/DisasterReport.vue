<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { ElMessage, type FormInstance, type UploadRequestOptions } from 'element-plus'
import { useDisasterStore } from '@/stores/disaster'
import { uploadFiles } from '@/api/upload'
import type { DisasterType, DisasterLevel } from '@/types'

const disaster = useDisasterStore()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const images = ref<string[]>([])

const YN_CITIES = [
  '昆明市', '曲靖市', '玉溪市', '保山市', '昭通市', '丽江市', '普洱市', '临沧市',
  '楚雄州', '红河州', '文山州', '西双版纳州', '大理州', '德宏州', '怒江州', '迪庆州'
]
const CITY_GEO: Record<string, [number, number]> = {
  昆明市: [102.71, 25.04], 曲靖市: [103.83, 25.49], 玉溪市: [102.54, 24.35], 保山市: [99.16, 25.11],
  昭通市: [103.71, 27.34], 丽江市: [100.23, 26.87], 普洱市: [100.97, 24.06], 临沧市: [100.1, 23.88],
  楚雄州: [101.54, 25.04], 红河州: [103.37, 23.37], 文山州: [104.24, 23.37], 西双版纳州: [100.79, 22.0],
  大理州: [100.27, 25.61], 德宏州: [98.58, 24.43], 怒江州: [98.85, 25.85], 迪庆州: [99.71, 27.83]
}

const typeOptions: { label: string; value: DisasterType }[] = [
  { label: '地震', value: 'EARTHQUAKE' }, { label: '洪涝', value: 'FLOOD' },
  { label: '滑坡', value: 'LANDSLIDE' }, { label: '泥石流', value: 'DEBRIS_FLOW' },
  { label: '干旱', value: 'DROUGHT' }, { label: '森林火灾', value: 'FOREST_FIRE' },
  { label: '冰雹', value: 'HAIL' }, { label: '台风', value: 'TYPHOON' }
]
const levelOptions: { label: string; value: DisasterLevel }[] = [
  { label: 'I 级（特别重大）', value: 'I' }, { label: 'II 级（重大）', value: 'II' },
  { label: 'III 级（较大）', value: 'III' }, { label: 'IV 级（一般）', value: 'IV' }
]

const form = reactive({
  title: '',
  type: 'EARTHQUAKE' as DisasterType,
  level: 'III' as DisasterLevel,
  city: '昆明市',
  district: '',
  location: '',
  lng: 102.71,
  lat: 25.04,
  description: '',
  affectedPopulation: undefined as number | undefined,
  affectedArea: undefined as number | undefined,
  casualties: undefined as number | undefined
})

const rules = {
  title: [{ required: true, message: '请输入灾情标题', trigger: 'blur' }],
  type: [{ required: true, message: '请选择灾害类型', trigger: 'change' }],
  level: [{ required: true, message: '请选择灾情等级', trigger: 'change' }],
  city: [{ required: true, message: '请选择所在州市', trigger: 'change' }],
  district: [{ required: true, message: '请输入区/县', trigger: 'blur' }],
  location: [{ required: true, message: '请输入具体位置', trigger: 'blur' }],
  description: [{ required: true, message: '请输入灾情描述', trigger: 'blur' }]
}

const geoText = computed(() => `${form.lng.toFixed(4)}, ${form.lat.toFixed(4)}`)

function onCityChange(city: string) {
  const g = CITY_GEO[city]
  if (g) {
    form.lng = g[0]
    form.lat = g[1]
  }
}

// 自定义上传：转发到后端 /api/upload（MinIO）
async function customUpload(options: UploadRequestOptions) {
  const fd = new FormData()
  fd.append('file', options.file)
  try {
    const urls = await uploadFiles(fd)
    const url = urls[0]
    images.value.push(url)
    options.onSuccess({ url })
  } catch {
    options.onError(new Error('上传失败') as unknown as Parameters<typeof options.onError>[0])
  }
}

function handleRemove(file: any) {
  const url = file.response?.url || file.url
  images.value = images.value.filter((u) => u !== url)
}

async function onSubmit() {
  await formRef.value?.validate()
  submitting.value = true
  try {
    await disaster.report({
      title: form.title,
      type: form.type,
      level: form.level,
      city: form.city,
      district: form.district,
      location: form.location,
      lng: form.lng,
      lat: form.lat,
      description: form.description,
      affectedPopulation: form.affectedPopulation,
      affectedArea: form.affectedArea,
      casualties: form.casualties,
      images: images.value
    })
    ElMessage.success('上报成功，已进入「待核验」队列')
    formRef.value?.resetFields()
    images.value = []
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="report">
    <el-card class="page-card">
      <template #header><b>灾情上报</b><span class="text-muted">（上报后进入「待核验」工单状态）</span></template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" style="max-width: 880px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="灾情标题" prop="title">
              <el-input v-model="form.title" placeholder="如：XX县XX镇山体滑坡" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="灾害类型" prop="type">
              <el-select v-model="form.type" style="width: 100%">
                <el-option v-for="t in typeOptions" :key="t.value" :label="t.label" :value="t.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="灾情等级" prop="level">
              <el-select v-model="form.level" style="width: 100%">
                <el-option v-for="l in levelOptions" :key="l.value" :label="l.label" :value="l.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="所在州市" prop="city">
              <el-select v-model="form.city" filterable style="width: 100%" @change="onCityChange">
                <el-option v-for="c in YN_CITIES" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="区/县" prop="district">
              <el-input v-model="form.district" placeholder="如：漾濞县" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="具体位置" prop="location">
              <el-input v-model="form.location" placeholder="乡镇/村落/路段" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="坐标">
          <el-input :model-value="geoText" disabled />
          <span class="text-muted" style="margin-left: 8px">默认取州市中心，可后端对接逆地理编码</span>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="受影响人口">
              <el-input-number v-model="form.affectedPopulation" :min="0" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="受灾面积(km²)">
              <el-input-number v-model="form.affectedArea" :min="0" :precision="1" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="伤亡人数">
              <el-input-number v-model="form.casualties" :min="0" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="灾情描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="灾情概况、发展趋势、已采取措施等" />
        </el-form-item>
        <el-form-item label="现场图片">
          <el-upload
            list-type="picture-card"
            :http-request="customUpload"
            :on-remove="handleRemove"
            :file-list="images.map((u) => ({ url: u }))"
            accept="image/*"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <span class="text-muted" style="margin-left: 8px">上传图片将存储至 MinIO 对象存储</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="onSubmit">提交上报</el-button>
          <el-button @click="formRef?.resetFields()">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
