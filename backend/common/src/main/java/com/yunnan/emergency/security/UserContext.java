package com.yunnan.emergency.security;

public class UserContext {

    private static final ThreadLocal<LoginUser> HOLDER = new ThreadLocal<>();

    public static void set(LoginUser user) {
        HOLDER.set(user);
    }

    public static LoginUser get() {
        return HOLDER.get();
    }

    public static void clear() {
        HOLDER.remove();
    }

    public static Long getUserId() {
        LoginUser u = get();
        return u == null ? null : u.getId();
    }

    public static String getRole() {
        LoginUser u = get();
        return u == null ? null : u.getRoleKey();
    }

    public static String getUsername() {
        LoginUser u = get();
        return u == null ? null : u.getUsername();
    }

    public static String getRealName() {
        LoginUser u = get();
        return u == null ? null : u.getRealName();
    }
}
