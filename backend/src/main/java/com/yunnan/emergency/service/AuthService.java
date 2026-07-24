package com.yunnan.emergency.service;

import com.yunnan.emergency.common.BizException;
import com.yunnan.emergency.dto.LoginRequest;
import com.yunnan.emergency.dto.LoginResponse;
import com.yunnan.emergency.entity.Role;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.mapper.RoleMapper;
import com.yunnan.emergency.mapper.UserMapper;
import com.yunnan.emergency.security.JwtUtil;
import com.yunnan.emergency.security.LoginUser;
import com.yunnan.emergency.security.UserContext;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.bcrypt.BCrypt;
import org.springframework.stereotype.Service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;

@Service
public class AuthService {

    @Autowired
    private UserMapper userMapper;
    @Autowired
    private RoleMapper roleMapper;
    @Autowired
    private JwtUtil jwtUtil;

    public LoginResponse login(LoginRequest req) {
        QueryWrapper<User> q = new QueryWrapper<>();
        q.eq("username", req.getUsername());
        User u = userMapper.selectOne(q);
        if (u == null || !"ENABLED".equals(u.getStatus())) {
            throw new BizException(401, "用户不存在或已停用");
        }
        if (!BCrypt.checkpw(req.getPassword(), u.getPassword())) {
            throw new BizException(401, "密码错误");
        }
        Role role = roleMapper.selectById(u.getRoleId());
        String roleKey = role == null ? "" : role.getRoleKey();
        String roleName = role == null ? "" : role.getRoleName();
        String token = jwtUtil.generate(u.getId(), u.getUsername(), roleKey, u.getRealName());
        LoginResponse resp = new LoginResponse();
        resp.setToken(token);
        resp.setUsername(u.getUsername());
        resp.setRealName(u.getRealName());
        resp.setRoleKey(roleKey);
        resp.setRoleName(roleName);
        return resp;
    }

    public LoginResponse me() {
        LoginUser u = UserContext.get();
        if (u == null) {
            throw new BizException(401, "未登录");
        }
        User user = userMapper.selectById(u.getId());
        Role role = user == null ? null : roleMapper.selectById(user.getRoleId());
        LoginResponse resp = new LoginResponse();
        resp.setUsername(u.getUsername());
        resp.setRealName(u.getRealName());
        resp.setRoleKey(u.getRoleKey());
        resp.setRoleName(role == null ? "" : role.getRoleName());
        return resp;
    }
}
