<template>
  <div class="weather-panel">
    <div class="panel-header">
      <div class="panel-title">
        <el-icon :size="18"><Sunny /></el-icon>
        <span>气象信息</span>
        <span class="panel-sub">数据来源：中央气象局（天气后报）</span>
      </div>
      <div class="city-selector">
        <el-cascader
          v-model="selectedCity"
          :options="cityOptions"
          :props="cascaderProps"
          placeholder="选择城市/区县"
          size="small"
          filterable
          @change="handleCityChange"
          style="width: 220px"
        />
        <el-button type="primary" size="small" :icon="Search" :loading="loading" @click="loadWeather">
          查询天气
        </el-button>
        <el-button size="small" :icon="Refresh" @click="loadWeather" circle />
      </div>
    </div>

    <div class="weather-content">
      <!-- 加载中 -->
      <div v-if="loading" class="weather-loading">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <p>正在爬取天气数据...</p>
      </div>

      <!-- 错误提示 -->
      <div v-else-if="error" class="weather-error">
        <el-icon :size="32" color="#f56c6c"><WarnTriangleFilled /></el-icon>
        <p>{{ error }}</p>
        <el-button size="small" @click="loadWeather">重试</el-button>
      </div>

      <!-- 天气数据展示 -->
      <div v-else-if="weatherData && weatherData.forecast && weatherData.forecast.length" class="weather-forecast">
        <div class="current-city">
          <el-icon><Location /></el-icon>
          <span>{{ weatherData.city || currentCityLabel }}</span>
          <span class="update-time">更新于 {{ formatTime(weatherData.fetched_at) }}</span>
        </div>

        <div class="forecast-cards">
          <div
            v-for="(day, idx) in weatherData.forecast"
            :key="idx"
            class="forecast-card"
            :class="{ 'is-today': day.date_label === '今天' }"
          >
            <div class="day-label">
              <span class="label">{{ day.date_label }}</span>
              <span class="weekday">{{ day.weekday }}</span>
              <span class="date">{{ day.date }}</span>
            </div>

            <div class="day-weather">
              <div class="weather-icon">{{ getWeatherIcon(day.day_weather) }}</div>
              <div class="weather-info">
                <div class="period">白天</div>
                <div class="weather-text">{{ day.day_weather || '-' }}</div>
                <div class="temp">{{ day.day_temp || '-' }}</div>
                <div class="wind">{{ day.day_wind || '-' }}</div>
              </div>
            </div>

            <div class="night-weather">
              <div class="weather-icon">{{ getWeatherIcon(day.night_weather) }}</div>
              <div class="weather-info">
                <div class="period">夜间</div>
                <div class="weather-text">{{ day.night_weather || '-' }}</div>
                <div class="temp">{{ day.night_temp || '-' }}</div>
                <div class="wind">{{ day.night_wind || '-' }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="weather-empty">
        <el-icon :size="32" color="#909399"><Cloudy /></el-icon>
        <p>请选择城市查询天气</p>
        <p class="hint">支持云南省16个地州市的所有区县</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Sunny, Cloudy, Location, Search, Refresh, Loading, WarnTriangleFilled
} from '@element-plus/icons-vue'
import { getWeatherCities, getWeatherForecast } from '@/api'

const loading = ref(false)
const error = ref('')
const weatherData = ref(null)
const cityTree = ref([])
const selectedCity = ref(['曲靖', '曲靖'])

const cascaderProps = {
  value: 'name',
  label: 'name',
  children: 'districts',
  emitPath: true
}

const currentCityLabel = computed(() => {
  if (Array.isArray(selectedCity.value) && selectedCity.value.length) {
    return selectedCity.value[selectedCity.value.length - 1]
  }
  return '未选择'
})

const cityOptions = computed(() => {
  return cityTree.value.map(city => ({
    name: city.city,
    districts: city.districts.map(d => ({ name: d.name, slug: d.slug }))
  }))
})

function getWeatherIcon(weather) {
  if (!weather) return '🌤️'
  if (weather.includes('晴')) return '☀️'
  if (weather.includes('多云')) return '⛅'
  if (weather.includes('阴')) return '☁️'
  if (weather.includes('雨')) {
    if (weather.includes('大') || weather.includes('暴')) return '🌧️'
    if (weather.includes('雷')) return '⛈️'
    return '🌦️'
  }
  if (weather.includes('雪')) return '❄️'
  if (weather.includes('雾') || weather.includes('霾')) return '🌫️'
  return '🌤️'
}

function formatTime(time) {
  if (!time) return ''
  return time.replace('T', ' ')
}

async function loadCities() {
  try {
    const res = await getWeatherCities()
    if (res.code === 200 && res.data?.cities) {
      cityTree.value = res.data.cities
    } else if (res.success && res.data?.cities) {
      cityTree.value = res.data.cities
    }
  } catch (e) {
    console.error('加载城市列表失败:', e)
  }
}

async function loadWeather() {
  if (!selectedCity.value || !selectedCity.value.length) {
    ElMessage.warning('请选择城市')
    return
  }

  loading.value = true
  error.value = ''

  try {
    const city = selectedCity.value[selectedCity.value.length - 1]
    const res = await getWeatherForecast({ city })

    let data = null
    if (res.code === 200 && res.data) {
      data = res.data.data || res.data
    } else if (res.success && res.data) {
      data = res.data
    }

    if (data && data.forecast) {
      weatherData.value = data
    } else if (data && data.error) {
      error.value = data.error
    } else {
      error.value = '未获取到天气数据'
    }
  } catch (e) {
    console.error('查询天气失败:', e)
    error.value = '查询天气失败：' + (e.message || '服务异常')
  } finally {
    loading.value = false
  }
}

function handleCityChange(val) {
  if (val && val.length) {
    loadWeather()
  }
}

onMounted(() => {
  loadCities()
  // 默认加载曲靖天气
  setTimeout(() => {
    loadWeather()
  }, 300)
})
</script>

<style scoped lang="scss">
.weather-panel {
  background: linear-gradient(135deg, #e3f2fd 0%, #f0f7ff 100%);
  border-radius: 10px;
  padding: 16px 20px;
  margin-top: 16px;
  border: 1px solid #bbdefb;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1976d2;

  .panel-sub {
    font-size: 12px;
    color: #909399;
    font-weight: normal;
    margin-left: 8px;
  }
}

.city-selector {
  display: flex;
  gap: 8px;
  align-items: center;
}

.weather-content {
  min-height: 180px;
}

.weather-loading,
.weather-error,
.weather-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  gap: 12px;
  color: #606266;

  p {
    margin: 0;
    font-size: 14px;
  }

  .hint {
    font-size: 12px;
    color: #909399;
  }
}

.current-city {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;

  .update-time {
    margin-left: auto;
    font-size: 12px;
    font-weight: normal;
    color: #909399;
  }
}

.forecast-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.forecast-card {
  background: #fff;
  border-radius: 8px;
  padding: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e3f2fd;
  transition: all 0.3s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(25, 118, 210, 0.15);
  }

  &.is-today {
    background: linear-gradient(135deg, #fff 0%, #e3f2fd 100%);
    border-color: #1976d2;
  }
}

.day-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-bottom: 10px;
  border-bottom: 1px dashed #e0e0e0;
  margin-bottom: 10px;

  .label {
    font-size: 14px;
    font-weight: 600;
    color: #1976d2;
  }

  .weekday {
    font-size: 12px;
    color: #606266;
    margin-top: 2px;
  }

  .date {
    font-size: 11px;
    color: #909399;
    margin-top: 2px;
  }
}

.day-weather,
.night-weather {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;

  &.night-weather {
    border-top: 1px dashed #f0f0f0;
    margin-top: 4px;
    padding-top: 8px;
  }
}

.weather-icon {
  font-size: 24px;
  line-height: 1;
}

.weather-info {
  flex: 1;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 2px 8px;
  font-size: 12px;

  .period {
    color: #909399;
    grid-column: 1;
  }

  .weather-text {
    color: #303133;
    grid-column: 2;
  }

  .temp {
    color: #f56c6c;
    font-weight: 600;
    grid-column: 1;
  }

  .wind {
    color: #606266;
    grid-column: 2;
    font-size: 11px;
  }
}

@media (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    align-items: stretch;
  }

  .city-selector {
    flex-wrap: wrap;
  }

  .forecast-cards {
    grid-template-columns: 1fr;
  }
}
</style>
