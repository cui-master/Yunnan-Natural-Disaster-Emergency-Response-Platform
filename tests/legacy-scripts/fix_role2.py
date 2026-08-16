file_path = r'f:\桌面\disaster\frontend\src\layouts\HorizontalLayout.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 改回 role（auth.js 已经把 roleCode 映射为 role）
old = 'const role = userStore.userInfo?.roleCode'
new = 'const role = userStore.userInfo?.role'

if old in content:
    content = content.replace(old, new)
    print('已改回 role')
else:
    print('未找到')

# 同时修复 defaultPath 中的 role 引用
old2 = 'const role = userStore.userInfo?.roleCode'
if old2 in content:
    content = content.replace(old2, 'const role = userStore.userInfo?.role')
    print('defaultPath 也修复了')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'文件已保存')
