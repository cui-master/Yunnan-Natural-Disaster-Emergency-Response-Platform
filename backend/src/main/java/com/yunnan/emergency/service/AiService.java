package com.yunnan.emergency.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import cn.hutool.http.HttpRequest;
import cn.hutool.http.HttpResponse;
import cn.hutool.json.JSONUtil;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
public class AiService {

    private static final Logger log = LoggerFactory.getLogger(AiService.class);

    @Value("${ai-service.base-url}")
    private String aiServiceBaseUrl;

    @Value("${ai-service.timeout:30000}")
    private Integer timeout;

    public String get(String path) {
        String url = aiServiceBaseUrl + path;
        log.debug("AI Service GET: {}", url);
        try {
            HttpResponse response = HttpRequest.get(url)
                .timeout(timeout)
                .execute();
            return response.body();
        } catch (Exception e) {
            log.error("AI Service GET failed: {}", url, e);
            throw new RuntimeException("AI服务调用失败: " + e.getMessage());
        }
    }

    public String post(String path, Object body) {
        String url = aiServiceBaseUrl + path;
        String jsonBody = body instanceof String ? (String) body : JSONUtil.toJsonStr(body);
        log.debug("AI Service POST: {}", url);
        try {
            HttpResponse response = HttpRequest.post(url)
                .header("Content-Type", "application/json")
                .body(jsonBody)
                .timeout(timeout)
                .execute();
            return response.body();
        } catch (Exception e) {
            log.error("AI Service POST failed: {}", url, e);
            throw new RuntimeException("AI服务调用失败: " + e.getMessage());
        }
    }

    public String postWithParams(String path, Map<String, Object> params) {
        String url = aiServiceBaseUrl + path;
        log.debug("AI Service POST params: {}", url);
        try {
            HttpResponse response = HttpRequest.post(url)
                .form(params)
                .timeout(timeout)
                .execute();
            return response.body();
        } catch (Exception e) {
            log.error("AI Service POST params failed: {}", url, e);
            throw new RuntimeException("AI服务调用失败: " + e.getMessage());
        }
    }

    public String uploadFile(String path, String fileParamName, byte[] fileBytes, String filename,
                              Map<String, Object> formParams) {
        String url = aiServiceBaseUrl + path;
        log.debug("AI Service UPLOAD: {}", url);
        try {
            HttpRequest request = HttpRequest.post(url)
                .timeout(timeout)
                .form(fileParamName, fileBytes, filename);
            if (formParams != null) {
                for (Map.Entry<String, Object> entry : formParams.entrySet()) {
                    request.form(entry.getKey(), entry.getValue());
                }
            }
            HttpResponse response = request.execute();
            return response.body();
        } catch (Exception e) {
            log.error("AI Service UPLOAD failed: {}", url, e);
            throw new RuntimeException("AI服务调用失败: " + e.getMessage());
        }
    }

    public String delete(String path) {
        String url = aiServiceBaseUrl + path;
        log.debug("AI Service DELETE: {}", url);
        try {
            HttpResponse response = HttpRequest.delete(url)
                .timeout(timeout)
                .execute();
            return response.body();
        } catch (Exception e) {
            log.error("AI Service DELETE failed: {}", url, e);
            throw new RuntimeException("AI服务调用失败: " + e.getMessage());
        }
    }

    // 健康检查
    public boolean checkHealth() {
        try {
            String result = get("/health");
            return result != null && result.contains("ok");
        } catch (Exception e) {
            log.warn("AI Service health check failed: {}", e.getMessage());
            return false;
        }
    }

    // 检查Dify工作流状态
    public Map<String, Object> checkDifyWorkflowStatus() {
        try {
            String result = get("/api/v1/admin/dify-status");
            return JSONUtil.toBean(result, Map.class);
        } catch (Exception e) {
            log.warn("检查Dify工作流状态失败: {}", e.getMessage());
            return Map.of(
                "status", "disconnected",
                "message", "AI服务不可用: " + e.getMessage(),
                "workflows", Map.of()
            );
        }
    }
}
