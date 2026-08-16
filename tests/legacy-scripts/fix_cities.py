file_path = r'f:\桌面\disaster\frontend\src\views\reporter\Report.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复：cities 只取城市名称字符串数组
old1 = '''  getWeatherCities().then(res => {
    if (res.data?.cities) cities.value = res.data.cities
  }).catch(() => {})'''

new1 = '''  getWeatherCities().then(res => {
    if (res.data?.cities) {
      // 只取城市名称，用于下拉框显示
      cities.value = res.data.cities.map(c => c.city)
    }
  }).catch(() => {})'''

if old1 in content:
    content = content.replace(old1, new1)
    print('1. cities 修复成功')
else:
    print('1. 未找到 old1')

# 修复区县加载：用城市名查找对应的 districts
old2 = '''    getWeatherDistricts(newCity).then(res => {
      if (res.data?.districts) {
        // 去掉第一个（城市本级，天气数据的第一个是城市本身）
        const list = res.data.districts
        if (list.length > 0 && list[0].name === newCity) {
          districts.value = list.slice(1)
        } else {
          districts.value = list
        }
      }
    }).catch(() => {})'''

new2 = '''    getWeatherDistricts(newCity).then(res => {
      if (res.data?.districts) {
        const list = res.data.districts
        // 去掉第一个（城市本级）
        if (list.length > 0 && list[0].name === newCity) {
          districts.value = list.slice(1)
        } else {
          districts.value = list
        }
      }
    }).catch(() => {})'''

if old2 in content:
    content = content.replace(old2, new2)
    print('2. 区县加载修复成功')
else:
    print('2. 未找到 old2')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'文件已保存，长度: {len(content)}')
