file_path = r'f:\桌面\disaster\frontend\src\layouts\HorizontalLayout.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old = '''    commander: [
      { path: '/commander/dashboard', title: '灾情态势大屏', icon: 'DataLine' },
      { path: '/commander/review', title: '审核事件', icon: 'CircleCheck' },
      { path: '/commander/plan', title: '处置方案', icon: 'Document' },
      { path: '/commander/dispatch', title: '调度看板', icon: 'Share' },
      { path: '/commander/resources', title: '救援资源查询', icon: 'Search' },
      { path: '/commander/report', title: '灾情上报', icon: 'EditPen' }
    ]'''

new = '''    commander: [
      { path: '/commander/dashboard', title: '灾情态势大屏', icon: 'DataLine' },
      { path: '/commander/report', title: '灾情上报', icon: 'EditPen' },
      { path: '/commander/review', title: '审核事件', icon: 'CircleCheck' },
      { path: '/commander/dispatch', title: '调度看板', icon: 'Share' },
      { path: '/commander/resources', title: '救援资源', icon: 'Search' },
      { path: '/commander/plan', title: '处置方案', icon: 'Document' }
    ]'''

if old in content:
    content = content.replace(old, new)
    print('菜单顺序调整成功')
else:
    print('未找到 old')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'文件已保存，长度: {len(content)}')
