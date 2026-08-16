package com.yunnan.emergency.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.yunnan.emergency.entity.Role;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.mapper.RoleMapper;
import com.yunnan.emergency.mapper.UserMapper;
import com.yunnan.emergency.service.UserService;
import com.yunnan.emergency.utils.JwtUtils;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {
    public UserServiceImpl(UserMapper userMapper, RoleMapper roleMapper, JwtUtils jwtUtils, BCryptPasswordEncoder passwordEncoder) {
        this.userMapper = userMapper;
        this.roleMapper = roleMapper;
        this.jwtUtils = jwtUtils;
        this.passwordEncoder = passwordEncoder;
    }


    private final UserMapper userMapper;
    private final RoleMapper roleMapper;
    private final JwtUtils jwtUtils;
    private final BCryptPasswordEncoder passwordEncoder;

    @Override
    public User login(String username, String password) {
        User user = getUserByUsername(username);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }
        if (user.getStatus() == 0) {
            throw new RuntimeException("用户已被禁用");
        }
        if (!passwordEncoder.matches(password, user.getPassword())) {
            throw new RuntimeException("密码错误");
        }

        String token = jwtUtils.generateToken(user.getId(), user.getUsername(), user.getRoleCode());
        user.setToken(token);

        Role role = roleMapper.selectOne(
            new LambdaQueryWrapper<Role>().eq(Role::getRoleCode, user.getRoleCode())
        );
        if (role != null) {
            user.setRoleName(role.getRoleName());
        }

        user.setLastLoginAt(LocalDateTime.now());
        userMapper.updateById(user);

        return user;
    }

    @Override
    public User getUserByUsername(String username) {
        return userMapper.selectOne(
            new LambdaQueryWrapper<User>().eq(User::getUsername, username)
        );
    }

    @Override
    public User getUserInfo(Long userId) {
        User user = userMapper.selectById(userId);
        if (user != null) {
            Role role = roleMapper.selectOne(
                new LambdaQueryWrapper<Role>().eq(Role::getRoleCode, user.getRoleCode())
            );
            if (role != null) {
                user.setRoleName(role.getRoleName());
            }
        }
        return user;
    }
}
