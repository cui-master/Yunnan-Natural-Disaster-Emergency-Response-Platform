file_path = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\service\Neo4jService.java'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 @Slf4j 注解 + 添加 import
old_import = 'import lombok.RequiredArgsConstructor;\nimport lombok.extern.slf4j.Slf4j;'
new_import = 'import lombok.RequiredArgsConstructor;\nimport org.slf4j.Logger;\nimport org.slf4j.LoggerFactory;'

if old_import in content:
    content = content.replace(old_import, new_import)
    print('import 替换成功')
else:
    print('未找到 import')

# 替换类上的 @Slf4j 注解
old_anno = '@Slf4j\n@Service\n@RequiredArgsConstructor\npublic class Neo4jService {'
new_anno = '@Service\n@RequiredArgsConstructor\npublic class Neo4jService {\n\n    private static final Logger log = LoggerFactory.getLogger(Neo4jService.class);'

if old_anno in content:
    content = content.replace(old_anno, new_anno)
    print('注解替换成功')
else:
    print('未找到注解')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'文件已保存，长度: {len(content)}')
