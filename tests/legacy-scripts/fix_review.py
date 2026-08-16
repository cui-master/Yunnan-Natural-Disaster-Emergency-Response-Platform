file_path = r'f:\桌面\disaster\frontend\src\views\commander\Review.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复 loadData 方法的数据判断
old_load = '''async function loadData() {
  const res = await getReviewList()
  if (res.success) {
    reviewList.value = res.data.list.map(item => ({ ...item, assessLevel: 3 }))
    pendingCount.value = res.data.total
  }
}'''

new_load = '''async function loadData() {
  try {
    const res = await getReviewList({ status: 'pending', pageSize: 100 })
    if (res.code === 200 && res.data) {
      const list = res.data.records || res.data.list || []
      reviewList.value = list.map(item => ({
        id: item.id,
        title: item.title || '未命名',
        type: item.disasterType || '未知',
        level: item.riskLevel || '中',
        reporter: item.reporterName || '未知',
        address: item.locationName || item.address || '未知位置',
        time: item.createdAt ? item.createdAt.substring(0, 16) : '',
        description: item.description || '暂无描述',
        assessLevel: 3,
        status: item.status
      }))
      pendingCount.value = res.data.total || list.length
    }
  } catch (e) {
    console.error('加载审核列表失败:', e)
  }
}'''

if old_load in content:
    content = content.replace(old_load, new_load)
    print('1. loadData 修复成功')
else:
    print('1. 未找到 old_load')

# 修复 handleReview 方法
old_review = '''  const res = await reviewEvent({ id: item.id, action, level: item.level })
  if (res.success) {
    ElMessage.success(`已${actionText}`)
    reviewList.value = reviewList.value.filter(i => i.id !== item.id)
    pendingCount.value--
  }'''

new_review = '''  const status = action === 'pass' ? 'approved' : 'rejected'
  const res = await reviewEvent(item.id, status, '')
  if (res.code === 200) {
    ElMessage.success(`已${actionText}`)
    reviewList.value = reviewList.value.filter(i => i.id !== item.id)
    pendingCount.value--
  } else {
    ElMessage.error(res.message || `${actionText}失败`)
  }'''

if old_review in content:
    content = content.replace(old_review, new_review)
    print('2. handleReview 修复成功')
else:
    print('2. 未找到 old_review')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'文件已保存，长度: {len(content)}')
