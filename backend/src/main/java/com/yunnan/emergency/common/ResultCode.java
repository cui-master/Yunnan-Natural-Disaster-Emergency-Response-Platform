package com.yunnan.emergency.common;


public enum ResultCode {

    SUCCESS(200, "操作成功"),
    BAD_REQUEST(400, "请求参数错误"),
    UNAUTHORIZED(401, "未授权，请重新登录"),
    FORBIDDEN(403, "权限不足"),
    NOT_FOUND(404, "资源不存在"),
    INTERNAL_ERROR(500, "服务器内部错误"),

    // 用户相关 1xxx
    USER_NOT_FOUND(1001, "用户不存在"),
    USER_PASSWORD_ERROR(1002, "密码错误"),
    USER_DISABLED(1003, "用户已被禁用"),
    USER_ALREADY_EXISTS(1004, "用户名已存在"),
    USER_NOT_LOGIN(1005, "用户未登录"),
    TOKEN_EXPIRED(1006, "Token已过期"),
    TOKEN_INVALID(1007, "Token无效"),

    // 业务相关 2xxx
    INCIDENT_NOT_FOUND(2001, "灾情事件不存在"),
    RESOURCE_NOT_FOUND(2002, "资源不存在"),
    PLAN_NOT_FOUND(2003, "应急方案不存在"),
    REPORT_NOT_FOUND(2004, "上报记录不存在"),
    UPLOAD_FAILED(2005, "文件上传失败"),

    // 系统相关 3xxx
    DIFY_ERROR(3001, "Dify工作流调用失败"),
    NEO4J_ERROR(3002, "Neo4j操作失败"),
    MODEL_ERROR(3003, "模型调用失败");

    private final Integer code;
    private final String message;

    ResultCode(Integer code, String message) {
        this.code = code;
        this.message = message;
    }

    public Integer getCode() { return code; }
    public String getMessage() { return message; }
}
