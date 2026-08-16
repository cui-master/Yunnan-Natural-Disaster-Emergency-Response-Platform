file_path = r'f:\桌面\disaster\frontend\src\views\reporter\Report.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 2. 在第二行（坐标/受灾人口/伤亡）后面添加道路名称
old_row2 = '''        <el-row :gutter="16">
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="坐标（经纬度）">
              <el-input v-model="form.coordinate" placeholder="102.7100, 25.0400">
                <template #append>
                  <el-button :icon="Location" @click="locate">定位</el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="受灾人口（人）" prop="affectedPeople">
              <el-input-number v-model="form.affectedPeople" :min="0" :max="999999" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="伤亡人数（人）" prop="casualties">
              <el-input-number v-model="form.casualties" :min="0" :max="9999" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>'''

new_row2 = '''        <el-row :gutter="16">
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="坐标（经纬度）">
              <el-input v-model="form.coordinate" placeholder="102.7100, 25.0400">
                <template #append>
                  <el-button :icon="Location" @click="locate">定位</el-button>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="受灾人口（人）" prop="affectedPeople">
              <el-input-number v-model="form.affectedPeople" :min="0" :max="999999" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="伤亡人数（人）" prop="casualties">
              <el-input-number v-model="form.casualties" :min="0" :max="9999" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="临近道路" prop="roadName">
              <el-input v-model="form.roadName" placeholder="如：昆磨高速、G214国道" />
            </el-form-item>
          </el-col>
        </el-row>'''

if old_row2 in content:
    content = content.replace(old_row2, new_row2)
    print('2. 第二行（坐标/人口/道路）更新成功')
else:
    print('2. 未找到 old_row2')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'中间保存，长度: {len(content)}')
