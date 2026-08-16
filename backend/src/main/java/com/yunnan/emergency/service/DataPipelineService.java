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
public class DataPipelineService {

    private static final Logger log = LoggerFactory.getLogger(DataPipelineService.class);

    @Value("${data-pipeline.base-url}")
    private String baseUrl;

    @Value("${data-pipeline.timeout:30000}")
    private Integer timeout;

    public String get(String path) {
        String url = baseUrl + path;
        log.debug("DataPipeline GET: {}", url);
        try {
            HttpResponse response = HttpRequest.get(url)
                .timeout(timeout)
                .execute();
            return response.body();
        } catch (Exception e) {
            log.error("DataPipeline GET failed: {}", url, e);
            throw new RuntimeException("数据管道服务调用失败: " + e.getMessage());
        }
    }

    public String post(String path, Object body) {
        String url = baseUrl + path;
        String jsonBody = body instanceof String ? (String) body : JSONUtil.toJsonStr(body);
        log.debug("DataPipeline POST: {}", url);
        try {
            HttpResponse response = HttpRequest.post(url)
                .header("Content-Type", "application/json")
                .body(jsonBody)
                .timeout(timeout)
                .execute();
            return response.body();
        } catch (Exception e) {
            log.error("DataPipeline POST failed: {}", url, e);
            throw new RuntimeException("数据管道服务调用失败: " + e.getMessage());
        }
    }

    public String delete(String path) {
        String url = baseUrl + path;
        log.debug("DataPipeline DELETE: {}", url);
        try {
            HttpResponse response = HttpRequest.delete(url)
                .timeout(timeout)
                .execute();
            return response.body();
        } catch (Exception e) {
            log.error("DataPipeline DELETE failed: {}", url, e);
            throw new RuntimeException("数据管道服务调用失败: " + e.getMessage());
        }
    }

    public String uploadFile(String path, String fileParamName, byte[] fileBytes, String filename,
                              Map<String, Object> formParams) {
        String url = baseUrl + path;
        log.debug("DataPipeline UPLOAD: {}", url);
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
            log.error("DataPipeline UPLOAD failed: {}", url, e);
            throw new RuntimeException("数据管道服务调用失败: " + e.getMessage());
        }
    }

    public boolean checkHealth() {
        try {
            String result = get("/health");
            return result != null && result.contains("ok");
        } catch (Exception e) {
            log.warn("DataPipeline health check failed: {}", e.getMessage());
            return false;
        }
    }
}
