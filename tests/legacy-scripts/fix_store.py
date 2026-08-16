file_path = r'f:\桌面\disaster\frontend\src\store\user.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复 getRoleName：兼容 role 和 roleCode
old = "return roleNameMap[role || userInfo.value?.role] || '未知角色'"
new = "return roleNameMap[role || userInfo.value?.role || userInfo.value?.roleCode] || '未知角色'"

if old in content:
    content = content.replace(old, new)
    print('getRoleName 修复成功')
else:
    print('未找到 old')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'文件已保存，长度: {len(content)}')
