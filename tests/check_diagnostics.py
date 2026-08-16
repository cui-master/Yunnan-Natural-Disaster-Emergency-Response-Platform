import os, re

base = r'f:\桌面\disaster\backend\src\main\java'
issues = []

for root, dirs, files in os.walk(base):
    for fn in files:
        if not fn.endswith('.java'): continue
        fp = os.path.join(root, fn)
        with open(fp, 'r', encoding='utf-8') as f:
            c = f.read()
        rel = os.path.relpath(fp, base)
        
        # 检查残留的 Lombok 注解
        if '@Data' in c:
            issues.append(f'[Lombok @Data] {rel}')
        if '@Slf4j' in c:
            issues.append(f'[Lombok @Slf4j] {rel}')
        if '@RequiredArgsConstructor' in c:
            issues.append(f'[Lombok @RequiredArgsConstructor] {rel}')
        if '@Getter' in c:
            issues.append(f'[Lombok @Getter] {rel}')
        if '@Setter' in c:
            issues.append(f'[Lombok @Setter] {rel}')
        if '@AllArgsConstructor' in c:
            issues.append(f'[Lombok @AllArgsConstructor] {rel}')
        if '@NoArgsConstructor' in c:
            issues.append(f'[Lombok @NoArgsConstructor] {rel}')
        
        # 检查残留的 lombok import
        if 'import lombok' in c:
            issues.append(f'[lombok import] {rel}')
        
        # 检查 BOM
        if c.startswith('\ufeff'):
            issues.append(f'[BOM] {rel}')
        
        # 检查使用 log 但没定义
        uses_log = bool(re.search(r'\blog\.', c))
        has_log_def = 'private static final Logger log' in c
        has_slf4j = '@Slf4j' in c
        if uses_log and not has_log_def and not has_slf4j:
            issues.append(f'[missing log] {rel}')

if issues:
    print('Found ' + str(len(issues)) + ' issues:')
    for i in issues:
        print('  ' + i)
else:
    print('No issues found')