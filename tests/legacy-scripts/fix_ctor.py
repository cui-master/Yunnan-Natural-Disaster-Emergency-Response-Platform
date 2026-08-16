import os, re
base = r'f:\桌面\disaster\backend\src\main\java'
count = 0
for root, dirs, files in os.walk(base):
    for fn in files:
        if not fn.endswith('.java'): continue
        fp = os.path.join(root, fn)
        with open(fp, 'r', encoding='utf-8') as f: c = f.read()
        cn = fn[:-5]
        has_final = bool(re.search(r'\b(?:private|protected|public)\s+final\s+\w', c, re.MULTILINE))
        has_ctor = bool(re.search(r'public\s+' + re.escape(cn) + r'\s*\(', c))
        has_lombok = '@RequiredArgsConstructor' in c
        if has_final and not has_ctor and not has_lombok:
            fs = []
            for m in re.finditer(r'(?:private|protected|public)\s+final\s+(\w+[<>\w,?\s\.]*)\s+(\w+)\s*;', c, re.MULTILINE):
                fs.append((m.group(1).strip(), m.group(2).strip()))
            if fs:
                params = ', '.join([f'{t} {n}' for t, n in fs])
                assigns = '\n'.join([f'        this.{n} = {n};' for t, n in fs])
                ctor = f'\n    public {cn}({params}) {{\n{assigns}\n    }}\n'
                c = re.sub(r'(public\s+class\s+' + re.escape(cn) + r'\s*[^{]*\{)', r'\1' + ctor, c)
                with open(fp, 'w', encoding='utf-8') as f: f.write(c)
                count += 1
                print('ctor: ' + os.path.relpath(fp, base))
print('Done: ' + str(count))