package com.yunnan.emergency.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.yunnan.emergency.entity.Info;
import com.yunnan.emergency.mapper.InfoMapper;
import org.springframework.stereotype.Service;

@Service
public class InfoService extends ServiceImpl<InfoMapper, Info> {

    /**
     * 获取唯一 info 记录，不存在则初始化一条
     */
    public Info getOrInit() {
        Info info = lambdaQuery().last("LIMIT 1").one();
        if (info == null) {
            info = new Info();
            info.setTotalDisasters(0);
            info.setInProgress(0);
            info.setPending(0);
            info.setAffectedPeople(0);
            info.setAvailableResources(0);
            info.setRescueTeams(0);
            save(info);
        }
        return info;
    }

    /**
     * 更新 info 记录（按唯一记录 id）
     */
    public void updateInfo(Info info) {
        Info current = getOrInit();
        info.setId(current.getId());
        updateById(info);
    }
}
