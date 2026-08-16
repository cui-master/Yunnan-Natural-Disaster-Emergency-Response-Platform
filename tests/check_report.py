file_path = r'f:\桌面\disaster\frontend\src\views\reporter\Report.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f'原文件长度: {len(content)}')
print('有 el-form-item:', 'el-form-item' in content)
print('有 affectedPeople:', 'affectedPeople' in content)
