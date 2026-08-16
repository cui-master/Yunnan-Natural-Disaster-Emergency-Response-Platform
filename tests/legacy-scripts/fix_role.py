file_path = r'f:\桌面\disaster\frontend\src\layouts\HorizontalLayout.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复角色字段名：role -> roleCode
old = 'const role = userStore.userInfo?.role'
new = 'const role = userStore.userInfo?.roleCode'

if old in content:
    content = content.replace(old, new)
    print('HorizontalLayout: role -> roleCode 修复成功')
else:
    print('未找到 old')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'文件已保存，长度: {len(content)}')
