package com.yunnan.emergency.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.yunnan.emergency.common.BizException;
import com.yunnan.emergency.dto.RoleVO;
import com.yunnan.emergency.dto.SystemConfigVO;
import com.yunnan.emergency.dto.UserVO;
import com.yunnan.emergency.entity.Role;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.mysql.mapper.RoleMapper;
import com.yunnan.emergency.mysql.mapper.UserMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.bcrypt.BCrypt;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class SystemService {

    @Autowired
    private UserMapper userMapper;
    @Autowired
    private RoleMapper roleMapper;

    public Map<String, Object> listUsers() {
        List<User> users = userMapper.selectList(null);
        List<UserVO> vos = new ArrayList<>();
        for (User u : users) {
            vos.add(toVO(u));
        }
        Map<String, Object> m = new HashMap<>();
        m.put("list", vos);
        m.put("total", (long) vos.size());
        return m;
    }

    public UserVO createUser(Map<String, Object> body) {
        String username = (String) body.get("username");
        String realName = (String) body.get("realName");
        String password = (String) body.get("password");
        List<String> roles = body.get("roles") instanceof List ? (List<String>) body.get("roles") : null;
        if (username == null || username.trim().isEmpty() || roles == null || roles.isEmpty()) {
            throw new BizException(400, "请填写用户名并分配角色");
        }
        String roleKey = "ROLE_" + roles.get(0);
        Role role = roleMapper.selectOne(new QueryWrapper<Role>().eq("role_key", roleKey));
        if (role == null) throw new BizException(400, "角色不存在: " + roles.get(0));

        User exist = userMapper.selectOne(new QueryWrapper<User>().eq("username", username));
        if (exist != null) throw new BizException(400, "用户名已存在");

        User u = new User();
        u.setUsername(username);
        u.setRealName(realName);
        u.setPassword(BCrypt.hashpw(password, BCrypt.gensalt()));
        u.setRoleId(role.getId());
        u.setStatus("ENABLED");
        userMapper.insert(u);
        return toVO(u);
    }

    public UserVO updateUser(Long id, Map<String, Object> body) {
        User u = userMapper.selectById(id);
        if (u == null) throw new BizException(404, "用户不存在");
        if (body.get("realName") != null) u.setRealName((String) body.get("realName"));
        if (body.get("phone") != null) u.setPhone((String) body.get("phone"));
        List<String> roles = body.get("roles") instanceof List ? (List<String>) body.get("roles") : null;
        if (roles != null && !roles.isEmpty()) {
            String roleKey = "ROLE_" + roles.get(0);
            Role role = roleMapper.selectOne(new QueryWrapper<Role>().eq("role_key", roleKey));
            if (role == null) throw new BizException(400, "角色不存在: " + roles.get(0));
            u.setRoleId(role.getId());
        }
        if (body.get("password") != null && !((String) body.get("password")).trim().isEmpty()) {
            u.setPassword(BCrypt.hashpw((String) body.get("password"), BCrypt.gensalt()));
        }
        if (body.get("status") != null) u.setStatus((String) body.get("status"));
        userMapper.updateById(u);
        return toVO(u);
    }

    public List<RoleVO> listRoles() {
        List<Role> roles = roleMapper.selectList(null);
        List<RoleVO> vos = new ArrayList<>();
        for (Role r : roles) {
            RoleVO v = new RoleVO();
            v.setName(r.getRoleName());
            v.setKey(stripPrefix(r.getRoleKey()));
            v.setDescription(r.getDescription());
            vos.add(v);
        }
        return vos;
    }

    public List<SystemConfigVO> getConfig() {
        List<SystemConfigVO> list = new ArrayList<>();
        list.add(cfg(1L, "DIFY_BASE_URL", "http://10.141.131.251:8080", "AI", "Dify 工作流服务地址"));
        list.add(cfg(2L, "AI_READ_TIMEOUT", "120", "AI", "AI 调用读超时(秒)"));
        list.add(cfg(3L, "PLAN_APPROVE_ROLE", "ROLE_COMMANDER", "业务", "方案审批角色"));
        list.add(cfg(4L, "DEFAULT_PASSWORD", "123456", "安全", "新建用户默认密码"));
        return list;
    }

    public void updateConfig(List<SystemConfigVO> body) {
        // MVP：配置项为内存默认值，暂不做持久化
    }

    private SystemConfigVO cfg(Long id, String key, String value, String group, String remark) {
        SystemConfigVO c = new SystemConfigVO();
        c.setId(id);
        c.setKey(key);
        c.setValue(value);
        c.setGroup(group);
        c.setRemark(remark);
        return c;
    }

    private UserVO toVO(User u) {
        UserVO v = new UserVO();
        v.setId(u.getId());
        v.setUsername(u.getUsername());
        v.setRealName(u.getRealName());
        v.setPhone(u.getPhone());
        v.setStatus(u.getStatus());
        v.setCreatedAt(u.getCreatedAt());
        Role r = u.getRoleId() != null ? roleMapper.selectById(u.getRoleId()) : null;
        String rk = r == null ? null : r.getRoleKey();
        v.setRoles(rk == null ? new ArrayList<>() : Collections.singletonList(stripPrefix(rk)));
        return v;
    }

    private static String stripPrefix(String rk) {
        if (rk != null && rk.startsWith("ROLE_")) return rk.substring(5);
        return rk;
    }
}
