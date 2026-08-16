package com.yunnan.emergency.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.yunnan.emergency.entity.Incident;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface IncidentMapper extends BaseMapper<Incident> {
}
