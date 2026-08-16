file_path = r'f:\桌面\disaster\frontend\src\views\reporter\Report.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 在具体位置后面插入街道字段 - 把第一行el-row的3列改成4列布局有点挤，
#    把具体位置那列后面加一个街道列，调整栅格
old_row1 = '''        <el-row :gutter="16">
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="所在州市" prop="city">
              <el-select v-model="form.city" placeholder="请选择">
                <el-option
                  v-for="c in cities"
                  :key="c"
                  :label="c"
                  :value="c"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="区/县" prop="district">
              <el-select v-model="form.district" placeholder="请先选择州市">
                <el-option
                  v-for="d in districts"
                  :key="d.name || d"
                  :label="d.name || d"
                  :value="d.name || d"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="8">
            <el-form-item label="具体位置" prop="address">
              <el-input v-model="form.address" placeholder="乡村/街道/路段" />
            </el-form-item>
          </el-col>
        </el-row>'''

new_row1 = '''        <el-row :gutter="16">
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="所在州市" prop="city">
              <el-select v-model="form.city" placeholder="请选择">
                <el-option
                  v-for="c in cities"
                  :key="c"
                  :label="c"
                  :value="c"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="区/县" prop="district">
              <el-select v-model="form.district" placeholder="请先选择州市">
                <el-option
                  v-for="d in districts"
                  :key="d.name || d"
                  :label="d.name || d"
                  :value="d.name || d"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="街道/乡镇" prop="street">
              <el-input v-model="form.street" placeholder="如：XX街道/XX镇" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="具体位置" prop="address">
              <el-input v-model="form.address" placeholder="乡村/路段/受灾点" />
            </el-form-item>
          </el-col>
        </el-row>'''

if old_row1 in content:
    content = content.replace(old_row1, new_row1)
    print('1. 第一行（位置信息）更新成功')
else:
    print('1. 未找到 old_row1')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'中间保存，长度: {len(content)}')
