file_path = r'f:\桌面\disaster\frontend\src\views\reporter\Report.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 3. 更新 form 数据对象，添加 street 和 roadName
old_form = '''const form = reactive({
  title: '',
  disasterType: '',
  riskLevel: '',
  urgentLevel: 3,
  city: '',
  district: '',
  address: '',
  coordinate: '',
  affectedPeople: 0,
  casualties: 0,
  description: ''
})'''

new_form = '''const form = reactive({
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
})'''

if old_form in content:
    content = content.replace(old_form, new_form)
    print('3. form 数据更新成功')
else:
    print('3. 未找到 old_form')

# 4. 更新 handleReset，重置新字段
old_reset = '''function handleReset() {
  formRef.value?.resetFields()
  form.urgentLevel = 3
  form.city = '昆明市'
  form.coordinate = ''
  form.affectedPeople = 0
  form.casualties = 0
  fileList.value = []
}'''

new_reset = '''function handleReset() {
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
}'''

if old_reset in content:
    content = content.replace(old_reset, new_reset)
    print('4. handleReset 更新成功')
else:
    print('4. 未找到 old_reset')

# 5. 解析坐标，把 coordinate 拆成 lng/lat（如果有的话）
#    在 handleSubmit 中添加解析逻辑
old_submit = '''    const res = await reportDisaster({
      ...form,
      images: fileList.value.map(f => f.name),
      reporter: userStore.userInfo?.name,
      reportTime: new Date().toISOString()
    })'''

new_submit = '''    // 解析坐标
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
    })'''

if old_submit in content:
    content = content.replace(old_submit, new_submit)
    print('5. handleSubmit 坐标解析添加成功')
else:
    print('5. 未找到 old_submit')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'最终保存，长度: {len(content)}')
