package com.yunnan.emergency.security;

import com.yunnan.emergency.common.BizException;

public class Authz {

    public static void require(String... roles) {
        String current = UserContext.getRole();
        if (current == null) {
            throw new BizException(401, "未登录");
        }
        for (String r : roles) {
            if (r.equals(current)) {
                return;
            }
        }
        throw new BizException(403, "当前角色无权限执行该操作");
    }
}
