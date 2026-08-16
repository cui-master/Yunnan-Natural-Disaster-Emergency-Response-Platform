package com.yunnan.emergency.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.yunnan.emergency.entity.User;

public interface UserService extends IService<User> {

    User login(String username, String password);

    User getUserByUsername(String username);

    User getUserInfo(Long userId);
}
