import os, re
base = r'f:\桌面\disaster\backend\src\main\java'
count = 0
for root, dirs, files in os.walk(base):
    for fn in files:
        if not fn.endswith('.java'): continue
        fp = os.path.join(root, fn)
        with open(fp, 'r', encoding='utf-8') as f: c = f.read()
        cn = fn[:-5]
        if re.search(r'\blog\.', c) and 'private static final Logger log' not in c and '@Slf4j' not in c:
            if 'import org.slf4j.Logger;' not in c:
                c = re.sub(r'(import\s+[\w\.]+;\n)', r'import org.slf4j.Logger;\nimport org.slf4j.LoggerFactory;\n\1', c, count=1)
            c = re.sub(r'(public\s+(?:class|interface|enum)\s+' + re.escape(cn) + r'\s*[^{]*\{)', r'\1\n\n    private static final Logger log = LoggerFactory.getLogger(' + cn + '.class);', c)
            with open(fp, 'w', encoding='utf-8') as f: f.write(c)
            count += 1
            print('log: ' + os.path.relpath(fp, base))
print('Done: ' + str(count))