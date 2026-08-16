package com.yunnan.emergency.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yunnan.emergency.entity.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper extends BaseMapper<User> {
}
