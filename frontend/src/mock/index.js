const mock = {
  auth: {
    login({ username, password, role }) {
      const users = {
        reporter: { username: 'reporter', name: '李上报', role: 'reporter', id: 1, avatar: '' },
        commander: { username: 'commander', name: '王指挥', role: 'commander', id: 2, avatar: '' },
        resmanager: { username: 'resmanager', name: '赵资源', role: 'resmanager', id: 3, avatar: '' },
        admin: { username: 'admin', name: '孙管理员', role: 'admin', id: 4, avatar: '' }
      }
      const user = users[role]
      if (user && user.username === username && password === '123456') {
        return {
          success: true,
          data: {
            token: `mock-token-${role}-${Date.now()}`,
            userInfo: user
          }
        }
      }
      return { success: false, message: '用户名或密码错误' }
    },
    logout() {
      return { success: true }
    },
    getUserInfo() {
      return { success: true, data: {} }
    }
  },

  dashboard: {
    getStats() {
      return {
        success: true,
        data: {
          totalDisasters: 14,
          inProgress: 6,
          pending: 3,
          affectedPeople: 159000,
          availableResources: 6,
          rescueTeams: 10
        }
      }
    },
    getTypeDistribution() {
      return {
        success: true,
        data: [
          { name: '地震', value: 2, color: '#36cfc9' },
          { name: '山洪', value: 1, color: '#ffa940' },
          { name: '洪涝', value: 3, color: '#40a9ff' },
          { name: '崩塌', value: 1, color: '#b37feb' },
          { name: '泥石流', value: 2, color: '#73d13d' },
          { name: '滑坡', value: 3, color: '#f759ab' },
          { name: '暴雨', value: 2, color: '#ffd666' }
        ]
      }
    },
    getCityCount() {
      const cities = [
        '昆明市', '曲靖市', '玉溪市', '保山市', '昭通市',
        '丽江市', '普洱市', '临沧市', '楚雄州', '红河州',
        '文山州', '西双版纳', '大理州', '德宏州', '怒江州',
        '迪庆州'
      ]
      return {
        success: true,
        data: cities.map(city => ({
          name: city,
          value: +(Math.random() * 0.8 + 0.1).toFixed(2)
        }))
      }
    },
    getWeeklyTrend() {
      const days = []
      const today = new Date()
      for (let i = 6; i >= 0; i--) {
        const d = new Date(today)
        d.setDate(d.getDate() - i)
        days.push({
          date: `${d.getMonth() + 1}-${d.getDate()}`,
          count: Math.floor(Math.random() * 10 + 2)
        })
      }
      return { success: true, data: days }
    },
    getMapMarkers() {
      const disasters = [
        { id: 'd001', name: 'XX县山体滑坡', type: '滑坡', level: '高', lng: 102.72, lat: 25.04, address: '昆明市XX县' },
        { id: 'd002', name: 'XX镇暴雨洪涝', type: '洪涝', level: '中', lng: 103.2, lat: 25.5, address: '曲靖市XX镇' },
        { id: 'd003', name: 'XX村泥石流', type: '泥石流', level: '高', lng: 100.23, lat: 26.87, address: '丽江市XX村' },
        { id: 'd004', name: 'XX山区地震', type: '地震', level: '极高', lng: 101.5, lat: 27.3, address: '迪庆州XX乡' },
        { id: 'd005', name: 'XX乡山洪', type: '山洪', level: '中', lng: 104.1, lat: 24.8, address: '文山州XX乡' },
        { id: 'd006', name: 'XX路段崩塌', type: '崩塌', level: '低', lng: 99.2, lat: 25.1, address: '大理州XX镇' },
        { id: 'd007', name: 'XX县暴雨预警', type: '暴雨', level: '中', lng: 102.0, lat: 23.8, address: '玉溪市XX县' },
        { id: 'd008', name: 'XX村滑坡风险', type: '滑坡', level: '高', lng: 103.8, lat: 26.3, address: '昭通市XX村' },
        { id: 'd009', name: 'XX镇洪涝灾害', type: '洪涝', level: '极高', lng: 100.8, lat: 22.5, address: '普洱市XX镇' },
        { id: 'd010', name: 'XX乡泥石流风险', type: '泥石流', level: '中', lng: 98.9, lat: 24.5, address: '保山市XX乡' },
        { id: 'd011', name: 'XX县地震', type: '地震', level: '高', lng: 102.9, lat: 23.3, address: '红河州XX县' },
        { id: 'd012', name: 'XX路段暴雨', type: '暴雨', level: '低', lng: 101.2, lat: 24.9, address: '楚雄州XX镇' },
        { id: 'd013', name: 'XX村山洪爆发', type: '山洪', level: '高', lng: 98.5, lat: 27.6, address: '怒江州XX村' },
        { id: 'd014', name: 'XX镇山体崩塌', type: '崩塌', level: '中', lng: 99.8, lat: 24.0, address: '临沧市XX镇' }
      ]
      return { success: true, data: disasters }
    },
    getDisasterList() {
      const list = [
        { id: 'd001', title: 'XX县山体滑坡', type: '滑坡', level: '高', status: '处置中', address: '昆明市XX县', time: '2026-07-25 10:30' },
        { id: 'd002', title: 'XX镇暴雨洪涝', type: '洪涝', level: '中', status: '待审核', address: '曲靖市XX镇', time: '2026-07-25 11:15' },
        { id: 'd003', title: 'XX村泥石流', type: '泥石流', level: '高', status: '处置中', address: '丽江市XX村', time: '2026-07-25 09:45' },
        { id: 'd004', title: 'XX山区地震', type: '地震', level: '极高', status: '已完成', address: '迪庆州XX乡', time: '2026-07-24 22:10' },
        { id: 'd005', title: 'XX乡山洪', type: '山洪', level: '中', status: '待审核', address: '文山州XX乡', time: '2026-07-25 12:00' }
      ]
      return { success: true, data: { total: 14, list } }
    }
  },

  reporter: {
    report(data) {
      return {
        success: true,
        data: { id: `ds-${Date.now()}`, ...data, status: '待审核' }
      }
    },
    uploadImage() {
      return {
        success: true,
        data: { url: 'https://example.com/mock-image.jpg', name: 'upload.jpg' }
      }
    }
  },

  commander: {
    getReviewList() {
      const list = [
        { id: 'd002', title: 'XX镇暴雨洪涝', type: '洪涝', level: '中', reporter: '李上报', address: '曲靖市XX镇', time: '2026-07-25 11:15', description: '突发暴雨，河水上涨，部分农田被淹', status: '待审核' },
        { id: 'd005', title: 'XX乡山洪', type: '山洪', level: '中', reporter: '张信息', address: '文山州XX乡', time: '2026-07-25 12:00', description: '山区强降雨引发山洪，道路被冲毁', status: '待审核' },
        { id: 'd006', title: 'XX路段崩塌', type: '崩塌', level: '低', reporter: '王记录', address: '大理州XX镇', time: '2026-07-25 08:30', description: '公路边坡发生小型崩塌，无人员伤亡', status: '待审核' }
      ]
      return { success: true, data: { total: 3, list } }
    },
    reviewEvent(data) {
      return {
        success: true,
        data: { id: data.id, status: '已审核', riskLevel: data.level || '中', reviewedAt: new Date().toISOString() }
      }
    },
    generatePlan(data) {
      return {
        success: true,
        data: {
          id: `plan-${Date.now()}`,
          areaName: data.areaName,
          disasterType: data.disasterType,
          riskLevel: data.riskLevel,
          plan: {
            materials: [
              { name: '救灾帐篷', quantity: 500, unit: '顶', warehouse: 'XX中心仓库', distance: '12.5km', estimatedTime: '30分钟' },
              { name: '食品物资', quantity: 2000, unit: '份', warehouse: 'XX应急储备库', distance: '18.2km', estimatedTime: '45分钟' },
              { name: '饮用水', quantity: 3000, unit: '瓶', warehouse: 'XX中心仓库', distance: '12.5km', estimatedTime: '30分钟' },
              { name: '医疗物资', quantity: 100, unit: '箱', warehouse: 'XX医疗储备库', distance: '25.0km', estimatedTime: '60分钟' }
            ],
            teams: [
              { name: '省消防救援总队一支队', members: 80, distance: '15.3km', estimatedTime: '35分钟', status: '空闲' },
              { name: '武警云南总队应急分队', members: 120, distance: '22.1km', estimatedTime: '50分钟', status: '空闲' }
            ],
            shelters: [
              { name: 'XX县第一中学', capacity: 3000, available: 2850, distance: '5.2km' },
              { name: 'XX县体育中心', capacity: 5000, available: 4800, distance: '8.7km' }
            ],
            evacuation: {
              affectedPeople: 15000,
              suggestedRoute: '沿XX省道向西北方向转移',
              assemblyPoint: 'XX县第一中学'
            }
          },
          generatedAt: new Date().toISOString(),
          source: 'Dify工作流'
        }
      }
    },
    getPlanList() {
      const list = [
        { id: 'plan-001', areaName: 'XX山区', disasterType: '地震', riskLevel: '极高', status: '已生成', createdAt: '2026-07-24 22:30' },
        { id: 'plan-002', areaName: 'XX镇', disasterType: '洪涝', riskLevel: '高', status: '已修改', createdAt: '2026-07-25 10:15' }
      ]
      return { success: true, data: { total: 2, list } }
    },
    savePlan(data) {
      return { success: true, data: { ...data, updatedAt: new Date().toISOString() } }
    },
    getDispatchGraph() {
      const nodes = [
        { id: 1, label: 'XX灾区', group: '受灾点' },
        { id: 2, label: 'XX中心仓库', group: '物资仓库' },
        { id: 3, label: 'XX应急储备库', group: '物资仓库' },
        { id: 4, label: '消防一支队', group: '救援队伍' },
        { id: 5, label: '武警分队', group: '救援队伍' },
        { id: 6, label: 'XX县一中', group: '避难场所' },
        { id: 7, label: 'XX体育中心', group: '避难场所' },
        { id: 8, label: 'S308省道', group: '道路' },
        { id: 9, label: 'G56高速', group: '道路' }
      ]
      const edges = [
        { from: 2, to: 1, label: '物资调运' },
        { from: 3, to: 1, label: '物资调运' },
        { from: 4, to: 1, label: '救援前往' },
        { from: 5, to: 1, label: '救援前往' },
        { from: 1, to: 6, label: '人员转移' },
        { from: 1, to: 7, label: '人员转移' },
        { from: 2, to: 8, label: '临近' },
        { from: 8, to: 1, label: '服务' },
        { from: 3, to: 9, label: '临近' },
        { from: 9, to: 1, label: '服务' }
      ]
      return { success: true, data: { nodes, edges } }
    }
  },

  resource: {
    getList(params) {
      const types = {
        warehouse: [
          { id: 'w001', name: '云南省救灾物资储备中心', type: '省级', status: '正常', city: '昆明市', capacity: '5000吨', manager: '张主任', contact: '13800000001' },
          { id: 'w002', name: '曲靖市应急物资仓库', type: '市级', status: '正常', city: '曲靖市', capacity: '2000吨', manager: '李主任', contact: '13800000002' },
          { id: 'w003', name: '大理州救灾物资储备库', type: '州级', status: '正常', city: '大理州', capacity: '1500吨', manager: '王主任', contact: '13800000003' },
          { id: 'w004', name: '丽江市应急物资中心', type: '市级', status: '维修中', city: '丽江市', capacity: '1200吨', manager: '赵主任', contact: '13800000004' }
        ],
        team: [
          { id: 't001', name: '云南省消防救援总队', type: '消防部队', status: '空闲', city: '昆明市', members: 500, carryLimit: '重型装备', manager: '陈队长', contact: '13900000001' },
          { id: 't002', name: '武警云南总队应急分队', type: '武警部队', status: '已调度', city: '昆明市', members: 300, carryLimit: '中型装备', manager: '刘队长', contact: '13900000002' },
          { id: 't003', name: '云南省矿山救护队', type: '专业救援', status: '空闲', city: '曲靖市', members: 80, carryLimit: '专业设备', manager: '周队长', contact: '13900000003' },
          { id: 't004', name: '大理州森林消防支队', type: '森林消防', status: '训练中', city: '大理州', members: 150, carryLimit: '轻型装备', manager: '吴队长', contact: '13900000004' }
        ],
        shelter: [
          { id: 's001', name: '昆明市体育中心', type: '室内场馆', status: '可用', city: '昆明市', capacity: 10000, accommodated: 0, address: '昆明市呈贡区' },
          { id: 's002', name: 'XX县第一中学', type: '学校', status: '可用', city: '曲靖市', capacity: 3000, accommodated: 150, address: 'XX县城区' },
          { id: 's003', name: 'XX县体育馆', type: '室内场馆', status: '可用', city: '丽江市', capacity: 2000, accommodated: 0, address: 'XX县新区' },
          { id: 's004', name: '大理州会展中心', type: '室内场馆', status: '维修中', city: '大理州', capacity: 8000, accommodated: 0, address: '大理市下关' }
        ],
        material: [
          { id: 'm001', name: '救灾帐篷', type: '帐篷类', unit: '顶', weight: 25, suitable: '地震,洪涝,滑坡' },
          { id: 'm002', name: '折叠床', type: '生活用品', unit: '张', weight: 8, suitable: '地震,洪涝,泥石流' },
          { id: 'm003', name: '应急食品', type: '食品类', unit: '份', weight: 1, suitable: '地震,洪涝,暴雨,滑坡' },
          { id: 'm004', name: '饮用水', type: '食品类', unit: '瓶', weight: 0.5, suitable: '地震,洪涝,暴雨,泥石流' },
          { id: 'm005', name: '医疗急救包', type: '医疗类', unit: '个', weight: 2, suitable: '地震,山洪,滑坡,崩塌' }
        ]
      }
      const type = params?.type || 'warehouse'
      return { success: true, data: { total: types[type]?.length || 0, list: types[type] || [] } }
    },
    add(data) {
      return { success: true, data: { id: `new-${Date.now()}`, ...data } }
    },
    update(id, data) {
      return { success: true, data: { id, ...data } }
    },
    remove(id) {
      return { success: true, data: { id } }
    }
  },

  admin: {
    getKnowledgeList() {
      const list = [
        { id: 'kb001', name: '优化调度知识库', type: '优化调度', docCount: 128, status: '启用', createdAt: '2026-07-20', updatedAt: '2026-07-24' },
        { id: 'kb002', name: '风险评估知识库', type: '风险评估', docCount: 86, status: '启用', createdAt: '2026-07-18', updatedAt: '2026-07-23' },
        { id: 'kb003', name: '应急响应规范', type: '应急管理', docCount: 45, status: '禁用', createdAt: '2026-07-15', updatedAt: '2026-07-20' },
        { id: 'kb004', name: '地质灾害案例库', type: '案例库', docCount: 200, status: '启用', createdAt: '2026-07-10', updatedAt: '2026-07-25' }
      ]
      return { success: true, data: { total: 4, list } }
    },
    addKnowledge(data) {
      return { success: true, data: { id: `kb-${Date.now()}`, ...data, status: '启用', docCount: 0 } }
    },
    updateKnowledge(id, data) {
      return { success: true, data: { id, ...data } }
    },
    deleteKnowledge(id) {
      return { success: true, data: { id } }
    },
    uploadDoc() {
      return { success: true, data: { url: '/mock-doc.pdf', name: 'upload.pdf' } }
    },

    getUserList() {
      const list = [
        { id: 1, username: 'reporter', name: '李上报', role: 'reporter', roleName: '普通信息员', status: '启用', lastLogin: '2026-07-25 08:00', phone: '13800000001' },
        { id: 2, username: 'commander', name: '王指挥', role: 'commander', roleName: '应急指挥员', status: '启用', lastLogin: '2026-07-25 07:30', phone: '13800000002' },
        { id: 3, username: 'resmanager', name: '赵资源', role: 'resmanager', roleName: '资源管理员', status: '启用', lastLogin: '2026-07-25 09:00', phone: '13800000003' },
        { id: 4, username: 'admin', name: '孙管理员', role: 'admin', roleName: '系统管理员', status: '启用', lastLogin: '2026-07-25 06:00', phone: '13800000004' }
      ]
      return { success: true, data: { total: 4, list } }
    },
    addUser(data) {
      return { success: true, data: { id: Date.now(), ...data, status: '启用' } }
    },
    updateUser(id, data) {
      return { success: true, data: { id, ...data } }
    },
    deleteUser(id) {
      return { success: true, data: { id } }
    },

    getModelList() {
      const list = [
        { id: 1, name: 'deepseek-v4-flash', provider: 'DeepSeek', type: 'LLM降级模型', status: '当前使用', apiBase: 'https://api.deepseek.com/v1', createdAt: '2026-07-01' },
        { id: 2, name: 'qwen-plus', provider: '通义千问', type: 'LLM降级模型', status: '备用', apiBase: 'https://dashscope.aliyuncs.com/compatible-mode/v1', createdAt: '2026-07-01' },
        { id: 3, name: 'qwen-max', provider: '通义千问', type: 'LLM降级模型', status: '禁用', apiBase: 'https://dashscope.aliyuncs.com/compatible-mode/v1', createdAt: '2026-07-10' }
      ]
      return { success: true, data: { total: 3, list } }
    },
    addModel(data) {
      return { success: true, data: { id: Date.now(), ...data, status: '备用' } }
    },
    updateModel(id, data) {
      return { success: true, data: { id, ...data } }
    },
    deleteModel(id) {
      return { success: true, data: { id } }
    },
    switchModel(id) {
      return { success: true, data: { id, status: '当前使用' } }
    }
  }
}

export default mock
