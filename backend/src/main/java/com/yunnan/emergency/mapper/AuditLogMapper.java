package com.yunnan.emergency.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yunnan.emergency.entity.AuditLog;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface AuditLogMapper extends BaseMapper<AuditLog> {
}
