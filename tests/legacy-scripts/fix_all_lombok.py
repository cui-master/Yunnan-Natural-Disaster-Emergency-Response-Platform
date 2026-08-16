import os
import re

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content
    class_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # @Slf4j
    if '@Slf4j\n' in content or 'import lombok.extern.slf4j.Slf4j;' in content:
        content = content.replace('import lombok.extern.slf4j.Slf4j;\n', '')
        content = content.replace('@Slf4j\n', '')
        if 'import org.slf4j.Logger;' not in content:
            content = re.sub(
                r'(import\s+[\w\.]+;\n)',
                r'import org.slf4j.Logger;\nimport org.slf4j.LoggerFactory;\n\1',
                content, count=1
            )
        content = re.sub(
            r'(public\s+class\s+' + re.escape(class_name) + r'\s*\{)',
            r'\1\n\n    private static final Logger log = LoggerFactory.getLogger(' + class_name + '.class);',
            content
        )
    
    # @RequiredArgsConstructor
    if '@RequiredArgsConstructor\n' in content:
        content = content.replace('import lombok.RequiredArgsConstructor;\n', '')
        content = content.replace('@RequiredArgsConstructor\n', '')
        final_fields = []
        final_pattern = re.compile(
            r'(?:@[\w\s.,()="\'\[\]]+\s+)*'
            r'(?:private|protected|public)\s+final\s+(\w+[<>\w,?\s\.]*)?\s+(\w+)\s*;',
            re.MULTILINE
        )
        for m in final_pattern.finditer(content):
            ftype = m.group(1) or 'String'
            fname = m.group(2)
            if ftype and fname:
                final_fields.append((ftype.strip(), fname.strip()))
        if final_fields:
            params = ', '.join([f'{ft} {fn}' for ft, fn in final_fields])
            assigns = '\n'.join([f'        this.{fn} = {fn};' for ft, fn in final_fields])
            constructor = f'\n    public {class_name}({params}) {{\n{assigns}\n    }}\n'
            content = re.sub(
                r'(public\s+class\s+' + re.escape(class_name) + r'\s*\{)',
                r'\1' + constructor,
                content
            )
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

base_dir = r'f:\桌面\disaster\backend\src\main\java'
count = 0
for root, dirs, files in os.walk(base_dir):
    for fname in files:
        if fname.endswith('.java'):
            fpath = os.path.join(root, fname)
            try:
                if process_file(fpath):
                    rel = os.path.relpath(fpath, base_dir)
                    print('OK: ' + rel)
                    count += 1
            except Exception as e:
                print('ERR: ' + fname + ' - ' + str(e))
print(f'\nDone: {count} files')