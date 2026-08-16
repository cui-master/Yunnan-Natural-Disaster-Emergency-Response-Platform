file_path = r'f:\桌面\disaster\frontend\src\views\reporter\Report.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 区县列表去掉第一个（城市本级）
old1 = '''    getWeatherDistricts(newCity).then(res => {
      if (res.data?.districts) districts.value = res.data.districts
    }).catch(() => {})'''

new1 = '''    getWeatherDistricts(newCity).then(res => {
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

if old1 in content:
    content = content.replace(old1, new1)
    print('1. 区县列表过滤成功')
else:
    print('1. 未找到 old1')

# 2. 道路字段设为必填 - 添加到 rules
old2 = '''  description: [{ required: true, message: '请填写灾害描述', trigger: 'blur' }]
}'''

new2 = '''  description: [{ required: true, message: '请填写灾害描述', trigger: 'blur' }],
  roadName: [{ required: true, message: '请填写临近道路', trigger: 'blur' }]
}'''

if old2 in content:
    content = content.replace(old2, new2)
    print('2. 道路必填规则添加成功')
else:
    print('2. 未找到 old2')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'文件已保存，长度: {len(content)}')
