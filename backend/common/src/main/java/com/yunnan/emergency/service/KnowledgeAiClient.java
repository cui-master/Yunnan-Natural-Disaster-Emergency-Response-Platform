package com.yunnan.emergency.service;

import com.yunnan.emergency.common.BizException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.util.HashMap;
import java.util.Map;

/**
 * 知识库（Dify Dataset）AI 服务调用客户端。
 *
 * 调用 ai_service 的 /api/v1/knowledge-base/* 端点，转发文件上传与删除。
 * 连接/读取超时 5s/120s，最多重试 3 次，退避 1s→2s→4s，耗尽抛 BizException(502)。
 */
@Service
public class KnowledgeAiClient {

    @Value("${ai.service.url:http://localhost:8001}")
    private String aiUrl;

    private RestTemplate buildRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000);
        factory.setReadTimeout(120000);
        return new RestTemplate(factory);
    }

    /** 上传单个文件到知识库，返回 {documentId, status, name} */
    @SuppressWarnings("unchecked")
    public Map<String, Object> upload(String kbName, String filename, byte[] content) {
        final int maxAttempts = 3;
        final long[] backoff = {1000, 2000, 4000};
        Exception last = null;
        for (int i = 0; i < maxAttempts; i++) {
            try {
                RestTemplate rt = buildRestTemplate();
                MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
                body.add("kb_name", kbName);
                ByteArrayResource resource = new ByteArrayResource(content) {
                    @Override
                    public String getFilename() {
                        return filename;
                    }
                };
                body.add("file", resource);
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.MULTIPART_FORM_DATA);
                HttpEntity<MultiValueMap<String, Object>> req = new HttpEntity<>(body, headers);

                ResponseEntity<Map> resp =
                        rt.postForEntity(aiUrl + "/api/v1/knowledge-base/upload", req, Map.class);
                Map<String, Object> bodyMap = resp.getBody();
                if (bodyMap == null) {
                    throw new BizException(502, "AI 服务返回为空");
                }
                Object resultObj = bodyMap.get("result");
                if (!(resultObj instanceof Map)) {
                    throw new BizException(502, "AI 服务返回缺少 result");
                }
                Map<String, Object> result = (Map<String, Object>) resultObj;
                Object documentObj = result.get("document");
                if (!(documentObj instanceof Map)) {
                    throw new BizException(502, "AI 服务返回缺少 document");
                }
                Map<String, Object> document = (Map<String, Object>) documentObj;
                String docId = String.valueOf(document.get("id"));
                String status = String.valueOf(document.getOrDefault("indexing_status", "PARSING"));
                String name = String.valueOf(document.getOrDefault("name", filename));

                Map<String, Object> out = new HashMap<>();
                out.put("documentId", docId);
                out.put("status", status);
                out.put("name", name);
                return out;
            } catch (BizException be) {
                throw be;
            } catch (Exception e) {
                last = e;
                if (i < maxAttempts - 1) {
                    try {
                        Thread.sleep(backoff[i]);
                    } catch (InterruptedException ignored) {
                        Thread.currentThread().interrupt();
                    }
                }
            }
        }
        throw new BizException(502, "知识库上传调用 AI 服务失败(已重试3次): " + (last == null ? "" : last.getMessage()));
    }

    /** 删除知识库文档（同时由调用方负责清理本地 knowledge_docs 表） */
    public void delete(String kbName, String docId) {
        try {
            RestTemplate rt = buildRestTemplate();
            String url = aiUrl + "/api/v1/knowledge-base/documents/" + docId
                    + "?kb_name=" + URLEncoder.encode(kbName, "UTF-8");
            rt.delete(url);
        } catch (UnsupportedEncodingException e) {
            throw new BizException(502, "知识库删除参数编码失败: " + e.getMessage());
        } catch (BizException be) {
            throw be;
        } catch (Exception e) {
            throw new BizException(502, "删除知识库文档失败: " + e.getMessage());
        }
    }
}
