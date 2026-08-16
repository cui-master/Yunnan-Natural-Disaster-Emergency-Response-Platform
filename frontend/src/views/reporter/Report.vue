<template>
  <div class="report-page">
    <div class="report-header">
      <div class="header-left">
        <el-icon :size="22" color="#e64545"><EditPen /></el-icon>
        <span class="header-title">灾情上报</span>
        <span class="header-sub">上报后进入「待审核」工单状态</span>
      </div>
      <div class="header-right">
        <span class="reporter-tag">
          <el-icon><User /></el-icon>
          {{ userStore.userInfo?.name }}
        </span>
        <span class="time-tag">
          <el-icon><Clock /></el-icon>
          {{ currentTime }}
        </span>
      </div>
    </div>

    <div class="report-card">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        label-position="top"
        class="report-form"
      >
        <!-- 灾害类型选择 -->
        <div class="form-section">
          <div class="section-title">
            <span class="required">*</span>灾害类型
          </div>
          <div class="type-grid">
            <div
              v-for="type in disasterTypes"
              :key="type.value"
              class="type-card"
              :class="{ active: form.disasterType === type.value }"
              @click="selectType(type.value)"
            >
              <div class="type-icon" :style="{ background: type.color + '15', color: type.color }">
                <el-icon :size="24"><component :is="type.icon" /></el-icon>
              </div>
              <span class="type-name">{{ type.label }}</span>
            </div>
          </div>
        </div>

        <el-row :gutter="16">
          <el-col :xs="24" :sm="24" :md="12">
            <el-form-item label="灾害标题" prop="title">
              <el-input v-model="form.title" placeholder="如：XX县XX山体滑坡灾害" maxlength="50" show-word-limit />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="灾害等级" prop="riskLevel">
              <el-select v-model="form.riskLevel" placeholder="请选择">
                <el-option label="低风险" value="低" />
                <el-option label="中风险" value="中" />
                <el-option label="高风险" value="高" />
                <el-option label="极高风险" value="极高" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="紧急程度" prop="urgentLevel">
              <el-rate v-model="form.urgentLevel" :max="5" :colors="['#52c41a', '#faad14', '#fa8c16', '#fa541c', '#f5222d']" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">位置信息</el-divider>

        <el-row :gutter="16">
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="所在州市" prop="city">
              <el-select v-model="form.city" placeholder="请选择">
                <el-option
                  v-for="c in cities"
                  :key="c"
                  :label="c"
                  :value="c"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="区/县" prop="district">
              <el-select v-model="form.district" placeholder="请先选择州市">
                <el-option
                  v-for="d in districts"
                  :key="d.name || d"
                  :label="d.name || d"
                  :value="d.name || d"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="街道/乡镇" prop="street">
              <el-input v-model="form.street" placeholder="如：XX街道/XX镇" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="具体位置" prop="address">
              <el-input v-model="form.address" placeholder="乡村/路段/受灾点" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="坐标（经纬度）">
              <el-input v-model="form.coordinate" placeholder="102.7100, 25.0400">
                <template #append>
                  <el-button :icon="Location" @click="locate">定位</el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="受灾人口（人）" prop="affectedPeople">
              <el-input-number v-model="form.affectedPeople" :min="0" :max="999999" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="伤亡人数（人）" prop="casualties">
              <el-input-number v-model="form.casualties" :min="0" :max="9999" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="临近道路" prop="roadName">
              <el-input v-model="form.roadName" placeholder="如：昆磨高速、G214国道" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">灾情描述</el-divider>

        <el-form-item label="灾害描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请详细描述灾情情况，包括灾害规模、影响范围、已采取的措施等"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="现场图片">
          <el-upload
            v-model:file-list="fileList"
            list-type="picture-card"
            :auto-upload="false"
            :limit="6"
            accept="image/*"
            :on-preview="handlePreview"
            :on-exceed="handleExceed"
          >
            <el-icon><Plus /></el-icon>
            <template #tip>
              <div class="upload-tip">支持 jpg/png 格式，单张不超过 5MB，最多 6 张</div>
            </template>
          </el-upload>
        </el-form-item>

        <div class="form-actions">
          <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
            <el-icon><Upload /></el-icon>
            提交上报
          </el-button>
          <el-button size="large" @click="handleReset">重置</el-button>
        </div>
      </el-form>
    </div>

    <!-- 图片预览 -->
    <el-dialog v-model="previewVisible" title="图片预览" width="60%">
      <img w-full :src="previewImage" alt="preview" style="width: 100%; border-radius: 8px;" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reportDisaster, getWeatherCities, getWeatherDistricts } from '@/api'
import { DISASTER_TYPES } from '@/utils/constants'
import dayjs from 'dayjs'
import {
  EditPen, User, Clock, Location, Plus, Upload
} from '@element-plus/icons-vue'

const userStore = useUserStore()
const formRef = ref(null)
const submitting = ref(false)
const currentTime = ref('')
const fileList = ref([])
const previewVisible = ref(false)
const previewImage = ref('')
let timer = null

const disasterTypes = DISASTER_TYPES

const cities = ref([])
const districts = ref([])

const form = reactive({
  title: '',
  disasterType: '',
  riskLevel: '',
  urgentLevel: 3,
  city: '',
  district: '',
  street: '',
  address: '',
  coordinate: '',
  affectedPeople: 0,
  casualties: 0,
  roadName: '',
  description: ''
})

const rules = {
  title: [{ required: true, message: '请输入灾害标题', trigger: 'blur' }],
  disasterType: [{ required: true, message: '请选择灾害类型', trigger: 'change' }],
  riskLevel: [{ required: true, message: '请选择灾害等级', trigger: 'change' }],
  city: [{ required: true, message: '请选择所在州市', trigger: 'change' }],
  address: [{ required: true, message: '请填写具体位置', trigger: 'blur' }],
  description: [{ required: true, message: '请填写灾害描述', trigger: 'blur' }],
  roadName: [{ required: true, message: '请填写临近道路', trigger: 'blur' }]
}

function selectType(type) {
  form.disasterType = type
}

function locate() {
  ElMessage.info('定位功能需接入高德地图 API')
}

function handlePreview(uploadFile) {
  previewImage.value = uploadFile.url
  previewVisible.value = true
}

function handleExceed() {
  ElMessage.warning('最多只能上传 6 张图片')
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    ElMessage.warning('请完善必填信息')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认提交灾情上报？提交后将进入待审核状态。`,
      '确认提交',
      { confirmButtonText: '确定提交', cancelButtonText: '再想想', type: 'warning' }
    )
  } catch {
    return
  }

  submitting.value = true
  try {
    // 解析坐标
    let lng = null, lat = null
    if (form.coordinate) {
      const parts = form.coordinate.split(/[,，\s]+/).filter(Boolean)
      if (parts.length >= 2) {
        lng = parseFloat(parts[0])
        lat = parseFloat(parts[1])
      }
    }
    const res = await reportDisaster({
      ...form,
      lng: isNaN(lng) ? null : lng,
      lat: isNaN(lat) ? null : lat,
      images: fileList.value.map(f => f.name),
      reporter: userStore.userInfo?.name,
      reportTime: new Date().toISOString()
    })
    if (res.success) {
      ElMessage.success('上报成功，等待审核')
      handleReset()
    } else {
      ElMessage.error(res.message || '上报失败')
    }
  } catch (e) {
    ElMessage.error('上报失败：' + (e.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

function handleReset() {
  formRef.value?.resetFields()
  form.urgentLevel = 3
  form.city = '昆明市'
  form.district = ''
  form.street = ''
  form.address = ''
  form.coordinate = ''
  form.affectedPeople = 0
  form.casualties = 0
  form.roadName = ''
  fileList.value = []
}

function updateTime() {
  currentTime.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  // 动态加载云南州市列表
  getWeatherCities().then(res => {
    if (res.data?.cities) {
      // 只取城市名称，用于下拉框显示
      cities.value = res.data.cities.map(c => c.city)
    }
  }).catch(() => {})
})

// 监听城市变化，动态加载区县
import { watch } from 'vue'
watch(() => form.city, (newCity) => {
  form.district = ''
  districts.value = []
  if (newCity) {
    getWeatherDistricts(newCity).then(res => {
      if (res.data?.districts) {
        const list = res.data.districts
        // 去掉第一个（城市本级）
        if (list.length > 0 && list[0].name === newCity) {
          districts.value = list.slice(1)
        } else {
          districts.value = list
        }
      }
    }).catch(() => {})
  }
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped lang="scss">
.report-page {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}

.report-header {
  background: #fff;
  border-radius: 8px 8px 0 0;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
  flex-wrap: wrap;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;

  .header-title {
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
  }

  .header-sub {
    font-size: 12px;
    color: #9ca3af;
    margin-left: 8px;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  color: #6b7280;
  font-size: 13px;

  .reporter-tag,
  .time-tag {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    background: #f3f4f6;
    border-radius: 20px;
  }

  .time-tag {
    font-family: 'Courier New', monospace;
  }
}

.report-card {
  background: #fff;
  border-radius: 0 0 8px 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.report-form {
  max-width: 1000px;
  margin: 0 auto;
}

.form-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 12px;

  .required {
    color: #f5222d;
    margin-right: 4px;
  }
}

.type-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 12px;

  @media (max-width: 900px) {
    grid-template-columns: repeat(4, 1fr);
  }

  @media (max-width: 500px) {
    grid-template-columns: repeat(3, 1fr);
  }
}

.type-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 8px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;

  &:hover {
    border-color: #e64545;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(230, 69, 69, 0.15);
  }

  &.active {
    border-color: #e64545;
    background: rgba(230, 69, 69, 0.04);
    box-shadow: 0 4px 12px rgba(230, 69, 69, 0.2);
  }
}

.type-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.type-name {
  font-size: 13px;
  color: #374151;
  font-weight: 500;
}

.upload-tip {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 8px;
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;

  .el-button {
    min-width: 140px;
  }
}

.required::before {
  content: '*';
  color: #f5222d;
  margin-right: 4px;
}

@media (max-width: 768px) {
  .report-page {
    padding: 0;
  }

  .report-header {
    padding: 12px 16px;
    border-radius: 0;
  }

  .report-card {
    padding: 16px;
    border-radius: 0;
  }

  .header-right {
    width: 100%;
    justify-content: flex-start;
  }

  .type-grid {
    gap: 8px;
  }

  .type-card {
    padding: 12px 4px;

    .type-icon {
      width: 40px;
      height: 40px;
    }

    .type-name {
      font-size: 12px;
    }
  }

  .form-actions {
    flex-direction: column;

    .el-button {
      width: 100%;
    }
  }
}
</style>
