package com.yunnan.emergency.controller;

import com.yunnan.emergency.common.R;
import com.yunnan.emergency.security.Authz;
import com.yunnan.emergency.security.UserContext;
import com.yunnan.emergency.service.KnowledgeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/knowledge")
public class KnowledgeController {

    @Autowired
    private KnowledgeService knowledgeService;

    /**
     * 多部件表单字段中文会被 Tomcat 按 ISO-8859-1 解码成乱码，这里防御性还原为 UTF-8。
     * 仅对合法知识库名做还原，其他字符串原样返回，不影响异常路径。
     */
    private String normalizeKbName(String kbName) {
        if (kbName == null) return null;
        if ("优化调度".equals(kbName) || "风险评估".equals(kbName)) return kbName;
        try {
            String fixed = new String(kbName.getBytes(StandardCharsets.ISO_8859_1), StandardCharsets.UTF_8);
            if ("优化调度".equals(fixed) || "风险评估".equals(fixed)) return fixed;
        } catch (Exception ignored) {
            // 还原失败则保留原值，交给后续校验
        }
        return kbName;
    }

    /** 知识库注册表（DB 为唯一真源），供前端下拉渲染 */
    @GetMapping("/bases")
    public R<List<Map<String, Object>>> bases() {
        Authz.require("ROLE_ADMIN");
        List<Map<String, Object>> list = knowledgeService.listBases().stream().map(kb -> {
            Map<String, Object> m = new HashMap<>();
            m.put("kbKey", kb.getKbKey());
            m.put("kbName", kb.getKbName());
            m.put("datasetId", kb.getDatasetId());
            m.put("description", kb.getDescription());
            return m;
        }).collect(Collectors.toList());
        return R.ok(list);
    }

    /** 上传文档（多部件：kbName + files[]） */
    @PostMapping("/upload")
    public R<Map<String, Object>> upload(
            @RequestParam("kbName") String kbName,
            @RequestParam("files") MultipartFile[] files) {
        Authz.require("ROLE_ADMIN");
        return R.ok(knowledgeService.upload(normalizeKbName(kbName), files, UserContext.getUsername()));
    }

    /** 列出某知识库文档 */
    @GetMapping("/documents")
    public R<Map<String, Object>> documents(@RequestParam("kbName") String kbName) {
        Authz.require("ROLE_ADMIN");
        return R.ok(knowledgeService.listDocuments(normalizeKbName(kbName)));
    }

    /** 删除文档（docId 为 Dify document id） */
    @DeleteMapping("/documents/{docId}")
    public R<?> delete(
            @PathVariable("docId") String docId,
            @RequestParam("kbName") String kbName) {
        Authz.require("ROLE_ADMIN");
        knowledgeService.deleteDocument(normalizeKbName(kbName), docId);
        return R.ok();
    }
}
