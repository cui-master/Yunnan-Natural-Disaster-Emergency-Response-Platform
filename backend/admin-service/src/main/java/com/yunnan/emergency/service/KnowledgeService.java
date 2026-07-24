package com.yunnan.emergency.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.yunnan.emergency.entity.KnowledgeBase;
import com.yunnan.emergency.entity.KnowledgeDoc;
import com.yunnan.emergency.mapper.KnowledgeBaseMapper;
import com.yunnan.emergency.mapper.KnowledgeMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class KnowledgeService {

    @Autowired
    private KnowledgeMapper knowledgeMapper;
    @Autowired
    private KnowledgeBaseMapper knowledgeBaseMapper;
    @Autowired
    private KnowledgeAiClient knowledgeAiClient;

    /** 列出知识库注册表（DB 为唯一真源） */
    public List<KnowledgeBase> listBases() {
        return knowledgeBaseMapper.selectList(null);
    }

    /**
     * 上传文档：逐个文件转发 ai_service → Dify，并把落库记录写入 knowledge_docs。
     * 返回结构对齐前端 KnowledgeKitUploadResp：{ msg, results:[{name, status}] }
     */
    public Map<String, Object> upload(String kbName, MultipartFile[] files, String uploader) {
        resolveBase(kbName);
        List<Map<String, Object>> results = new ArrayList<>();
        if (files != null) {
            for (MultipartFile f : files) {
                if (f == null || f.isEmpty()) continue;
                String filename = f.getOriginalFilename();
                byte[] content;
                try {
                    content = f.getBytes();
                } catch (Exception e) {
                    throw new RuntimeException("读取文件失败: " + e.getMessage());
                }
                Map<String, Object> r = knowledgeAiClient.upload(kbName, filename, content);

                KnowledgeDoc d = new KnowledgeDoc();
                d.setKbName(kbName);
                d.setDifyDocumentId(String.valueOf(r.get("documentId")));
                d.setDocName(filename);
                d.setStatus(String.valueOf(r.get("status")));
                d.setChunkCount(0);
                d.setWordCount(0);
                d.setUploader(uploader);
                d.setUploadedAt(LocalDateTime.now());
                d.setUpdatedAt(LocalDateTime.now());
                knowledgeMapper.insert(d);

                Map<String, Object> one = new HashMap<>();
                one.put("name", r.get("name"));
                one.put("status", r.get("status"));
                results.add(one);
            }
        }
        Map<String, Object> resp = new HashMap<>();
        resp.put("msg", "已提交 " + results.size() + " 个文件至【" + kbName + "】知识库，后台正在解析切片");
        resp.put("results", results);
        return resp;
    }

    /** 列出某知识库文档（DB 为唯一真源），对齐前端 KnowledgeKitDoc[] */
    public Map<String, Object> listDocuments(String kbName) {
        QueryWrapper<KnowledgeDoc> q = new QueryWrapper<>();
        q.eq("kb_name", kbName);
        q.orderByDesc("uploaded_at");
        List<KnowledgeDoc> docs = knowledgeMapper.selectList(q);
        List<Map<String, Object>> list = docs.stream().map(d -> {
            Map<String, Object> m = new HashMap<>();
            m.put("id", d.getDifyDocumentId());
            m.put("name", d.getDocName());
            m.put("status", d.getStatus());
            m.put("chunkCount", d.getChunkCount());
            m.put("wordCount", d.getWordCount());
            m.put("uploadedAt", fmt(d.getUploadedAt()));
            return m;
        }).collect(Collectors.toList());
        Map<String, Object> resp = new HashMap<>();
        resp.put("list", list);
        resp.put("total", list.size());
        return resp;
    }

    /** 删除：先调 ai_service 删 Dify 文档，再删本地 knowledge_docs 行 */
    public void deleteDocument(String kbName, String docId) {
        knowledgeAiClient.delete(kbName, docId);
        QueryWrapper<KnowledgeDoc> q = new QueryWrapper<>();
        q.eq("kb_name", kbName).eq("dify_document_id", docId);
        knowledgeMapper.delete(q);
    }

    private KnowledgeBase resolveBase(String kbName) {
        QueryWrapper<KnowledgeBase> q = new QueryWrapper<>();
        q.eq("kb_name", kbName);
        KnowledgeBase kb = knowledgeBaseMapper.selectOne(q);
        if (kb == null) {
            throw new RuntimeException("未知知识库：" + kbName + "，仅支持：优化调度 / 风险评估");
        }
        return kb;
    }

    private String fmt(LocalDateTime t) {
        return t == null ? null : t.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
    }
}
