import re

files = [
    r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\controller\AuthController.java',
    r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\service\EventPushService.java',
]

for fp in files:
    with open(fp, 'r', encoding='utf-8') as f:
        c = f.read()
    original = c
    # 删除所有 lombok 相关的 import
    c = re.sub(r'^import lombok\.[\w\.]+;\n', '', c, flags=re.MULTILINE)
    if c != original:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(c)
        print('Cleaned: ' + fp.split('\\\\')[-1])
    else:
        print('No change: ' + fp.split('\\\\')[-1])