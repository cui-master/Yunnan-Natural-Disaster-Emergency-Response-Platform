import re

# 处理 Result.java
file_path = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\common\Result.java'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('import lombok.Data;\n', '')
content = content.replace('@Data\n', '')

# 给 Result 添加 getter/setter
fields = [
    ('Integer', 'code'),
    ('String', 'message'),
    ('T', 'data'),
    ('Long', 'timestamp')
]
methods = []
for ftype, fname in fields:
    cap = fname[0].upper() + fname[1:]
    methods.append(f'    public {ftype} get{cap}() {{ return {fname}; }}')
    methods.append(f'    public void set{cap}({ftype} {fname}) {{ this.{fname} = {fname}; }}')

methods_str = '\n'.join(methods)
# 插入到构造函数之前
content = content.replace('    public Result() {}', methods_str + '\n\n    public Result() {}')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Result.java done')

# 处理 ResultCode.java
file_path2 = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\common\ResultCode.java'
with open(file_path2, 'r', encoding='utf-8') as f:
    content2 = f.read()

content2 = content2.replace('import lombok.Getter;\n', '')
content2 = content2.replace('@Getter\n', '')

# 给 ResultCode 添加 getter
rc_fields = [
    ('Integer', 'code'),
    ('String', 'message')
]
rc_methods = []
for ftype, fname in rc_fields:
    cap = fname[0].upper() + fname[1:]
    rc_methods.append(f'    public {ftype} get{cap}() {{ return {fname}; }}')

rc_methods_str = '\n'.join(rc_methods)
# 插入到第一个字段后
content2 = re.sub(
    r'(private Integer code;\s*private String message;)',
    r'\1\n\n' + rc_methods_str,
    content2
)

with open(file_path2, 'w', encoding='utf-8') as f:
    f.write(content2)
print('ResultCode.java done')
