file_path = r'f:\桌面\disaster\backend\src\main\java\com\yunnan\emergency\common\ResultCode.java'
with open(file_path, 'r', encoding='utf-8') as f:
    c = f.read()

# 在构造函数后添加 getter
old = '''    ResultCode(Integer code, String message) {
        this.code = code;
        this.message = message;
    }
}'''

new = '''    ResultCode(Integer code, String message) {
        this.code = code;
        this.message = message;
    }

    public Integer getCode() { return code; }
    public String getMessage() { return message; }
}'''

if old in c:
    c = c.replace(old, new)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(c)
    print('ResultCode getter added')
else:
    print('Pattern not found, checking...')
    # 检查是否已经有 getter
    if 'public Integer getCode()' in c:
        print('getter already exists')
    else:
        print('unknown issue')
