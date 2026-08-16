import os
import re

def gen_getter_setter(field_type, field_name):
    cap = field_name[0].upper() + field_name[1:]
    prefix = 'is' if field_type == 'boolean' else 'get'
    getter = '    public ' + field_type + ' ' + prefix + cap + '() { return ' + field_name + '; }'
    setter = '    public void set' + cap + '(' + field_type + ' ' + field_name + ') { this.' + field_name + ' = ' + field_name + '; }'
    return getter, setter

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if '@Data' not in content:
        return False
    content = content.replace('import lombok.Data;\n', '')
    content = content.replace('@Data\n', '')
    fields = []
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
        return False
    methods = []
    for ftype, fname in fields:
        g, s = gen_getter_setter(ftype, fname)
        methods.append(g)
        methods.append(s)
    methods_str = '\n'.join(methods)
    last_field_match = None
    for m in pattern.finditer(content):
        last_field_match = m
    if last_field_match:
        insert_pos = last_field_match.end()
        content = content[:insert_pos] + '\n\n' + methods_str + content[insert_pos:]
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return True

# 处理 config 目录下的 @Data 类
config_dir = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\config'
count = 0
for root, dirs, files in os.walk(config_dir):
    for fname in files:
        if fname.endswith('.java'):
            fpath = os.path.join(root, fname)
            try:
                if process_file(fpath):
                    print('OK: ' + fname)
                    count += 1
            except Exception as e:
                print('ERR: ' + fname + ' - ' + str(e))
print('Config Done: ' + str(count) + ' files')
