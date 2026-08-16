import os
import re

# 生成 getter/setter 的函数
def gen_getter_setter(field_type, field_name):
    # 首字母大写
    cap = field_name[0].upper() + field_name[1:]
    prefix = 'is' if field_type == 'boolean' else 'get'
    getter = f'    public {field_type} {prefix}{cap}() {{ return {field_name}; }}'
    setter = f'    public void set{cap}({field_type} {field_name}) {{ this.{field_name} = {field_name}; }}'
    return getter, setter

# 解析实体类，提取字段并生成 getter/setter
def process_entity(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 移除 @Data 注解
    content = content.replace('import lombok.Data;\n', '')
    content = content.replace('@Data\n', '')

    # 找到类的第一个字段（跳过 id 或 tableId 注解的字段）
    # 找到类定义的结束括号前，插入 getter/setter
    # 先提取所有字段定义
    fields = []
    # 匹配字段：private 类型 名称;  支持注解
    pattern = re.compile(
        r'(?:@[\w\s.,()=\"\'\[\]]+\s+)*'
        r'private\s+(\w+[<>\w,?\s\.]*)?\s+(\w+)\s*;',
        re.MULTILINE
    )
    for m in pattern.finditer(content):
        ftype = m.group(1) or 'String'
        fname = m.group(2)
        if ftype and fname:
            fields.append((ftype.strip(), fname.strip()))

    if not fields:
        print(f'  未找到字段，跳过')
        return False

    # 生成所有 getter/setter
    methods = []
    for ftype, fname in fields:
        g, s = gen_getter_setter(ftype, fname)
        methods.append(g)
        methods.append(s)

    methods_str = '\n'.join(methods)

    # 找到最后一个字段的结尾，插入方法
    # 找最后一个 private ...;
    last_field_match = None
    for m in pattern.finditer(content):
        last_field_match = m

    if last_field_match:
        insert_pos = last_field_match.end()
        # 插入到最后一个字段之后
        content = content[:insert_pos] + '\n\n' + methods_str + content[insert_pos:]
        print(f'  生成了 {len(fields)} 个字段的 getter/setter')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

# 处理所有实体类
entity_dir = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\entity'
for fname in os.listdir(entity_dir):
    if fname.endswith('.java') and fname != 'package-info.java':
        fpath = os.path.join(entity_dir, fname)
        print(f'处理 {fname}...')
        try:
            process_entity(fpath)
        except Exception as e:
            print(f'  错误: {e}')

print('实体类处理完成')
