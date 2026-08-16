import dayjs from 'dayjs'

export const DISASTER_TYPES = [
  { value: '地震', label: '地震', icon: 'warning', color: '#f5222d' },
  { value: '山洪', label: '山洪', icon: 'Watermelon', color: '#fa8c16' },
  { value: '洪涝', label: '洪涝', icon: 'Water', color: '#1890ff' },
  { value: '崩塌', label: '崩塌', icon: 'Aim', color: '#722ed1' },
  { value: '泥石流', label: '泥石流', icon: 'Histogram', color: '#52c41a' },
  { value: '滑坡', label: '滑坡', icon: 'Histogram', color: '#eb2f96' },
  { value: '暴雨', label: '暴雨', icon: 'Cloudy', color: '#faad14' }
]

export const RISK_LEVELS = [
  { value: '低', label: '低风险', color: '#52c41a' },
  { value: '中', label: '中风险', color: '#faad14' },
  { value: '高', label: '高风险', color: '#fa541c' },
  { value: '极高', label: '极高风险', color: '#f5222d' }
]

export const ROLE_MAP = {
  reporter: '普通信息员',
  commander: '应急指挥员',
  resmanager: '资源管理员',
  admin: '系统管理员'
}

export function formatDate(date, fmt = 'YYYY-MM-DD HH:mm') {
  return dayjs(date).format(fmt)
}

export function getDisasterColor(type) {
  const item = DISASTER_TYPES.find(d => d.value === type)
  return item?.color || '#999'
}

export function getRiskColor(level) {
  const item = RISK_LEVELS.find(r => r.value === level)
  return item?.color || '#999'
}
