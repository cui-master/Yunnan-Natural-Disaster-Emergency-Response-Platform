package com.yunnan.emergency.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.KnowledgeBase;
import com.yunnan.emergency.entity.KnowledgeBaseDocument;
import com.yunnan.emergency.mapper.KnowledgeBaseDocumentMapper;
import com.yunnan.emergency.mapper.KnowledgeBaseMapper;
import com.yunnan.emergency.service.AiService;
import com.yunnan.emergency.service.DataPipelineService;
import com.yunnan.emergency.service.DifyKnowledgeSyncService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import org.springframework.web.multipart.MultipartFile;

/**
 * 知识库管理 Controller
 *
 * 双写策略：
 *   - MySQL knowledge_bases 表（主存储，保证强一致）
 *   - Dify dataset API（同步创建/删除，kb_id 字段存 Dify 知识库 ID）
 *
 * 当 Dify 不可用时，SQL 操作仍成功（Dify 同步失败只记日志），保证主流程不中断。
 * 通过 /admin/knowledge-bases/dify-status 可查看 Dify 连通性。
 */
@Tag(name = "知识库管理", description = "Dify知识库的增删改查和同步")
@RestController
@RequestMapping("/admin/knowledge-bases")
public class KnowledgeBaseController {
    public KnowledgeBaseController(KnowledgeBaseMapper kbMapper,
                                    KnowledgeBaseDocumentMapper docMapper,
                                    DifyKnowledgeSyncService difySyncService,
                                    DataPipelineService dataPipelineService,
                                    AiService aiService) {
        this.kbMapper = kbMapper;
        this.docMapper = docMapper;
        this.difySyncService = difySyncService;
        this.dataPipelineService = dataPipelineService;
        this.aiService = aiService;
    }


    private static final Logger log = LoggerFactory.getLogger(KnowledgeBaseController.class);

    private final KnowledgeBaseMapper kbMapper;
    private final KnowledgeBaseDocumentMapper docMapper;
    private final DifyKnowledgeSyncService difySyncService;
    private final DataPipelineService dataPipelineService;
    private final AiService aiService;

    @Operation(summary = "分页查询知识库")
    @GetMapping("/page")
    public Result<Page<KnowledgeBase>> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) Integer status,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String keyword) {

        LambdaQueryWrapper<KnowledgeBase> wrapper = new LambdaQueryWrapper<>();
        if (status != null) {
            wrapper.eq(KnowledgeBase::getStatus, status);
        }
        if (category != null && !category.isEmpty()) {
            wrapper.eq(KnowledgeBase::getCategory, category);
        }
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.like(KnowledgeBase::getName, keyword);
        }
        wrapper.orderByDesc(KnowledgeBase::getCreatedAt);

        Page<KnowledgeBase> page = kbMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
        return Result.success(page);
    }

    @Operation(summary = "获取全部知识库列表")
    @GetMapping("/list")
    public Result<List<KnowledgeBase>> list(@RequestParam(required = false) Integer status) {
        LambdaQueryWrapper<KnowledgeBase> wrapper = new LambdaQueryWrapper<>();
        if (status != null) {
            wrapper.eq(KnowledgeBase::getStatus, status);
        }
        wrapper.orderByAsc(KnowledgeBase::getId);
        return Result.success(kbMapper.selectList(wrapper));
    }

    @Operation(summary = "获取知识库详情")
    @GetMapping("/{id}")
    public Result<KnowledgeBase> getById(@PathVariable Long id) {
        return Result.success(kbMapper.selectById(id));
    }

    @Operation(summary = "新增知识库（同步创建到 Dify）")
    @PostMapping
    public Result<KnowledgeBase> create(@RequestBody KnowledgeBase kb) {
        if (kb.getStatus() == null) {
            kb.setStatus(1);
        }
        if (kb.getDocumentCount() == null) {
            kb.setDocumentCount(0);
        }

        // 1. 同步创建到 Dify dataset
        try {
            Map<String, Object> difyResult = difySyncService.syncCreate(kb.getName(), kb.getDescription());
            Object difyId = difyResult.get("id");
            if (difyId != null) {
                kb.setKbId(String.valueOf(difyId));
                log.info("[kb] 同步创建 Dify 知识库成功: name={}, difyId={}", kb.getName(), difyId);
            }
        } catch (Exception e) {
            log.warn("[kb] 同步创建 Dify 知识库失败（SQL 仍继续）: name={}, err={}", kb.getName(), e.getMessage());
        }

        // 2. 写入 MySQL（若 Dify 失败，kb_id 留空，后续可手动补）
        if (kb.getKbId() == null || kb.getKbId().isBlank()) {
            kb.setKbId("pending-" + System.currentTimeMillis());
        }
        kbMapper.insert(kb);
        return Result.success(kb);
    }

    @Operation(summary = "更新知识库")
    @PutMapping("/{id}")
    public Result<KnowledgeBase> update(@PathVariable Long id, @RequestBody KnowledgeBase kb) {
        kb.setId(id);
        kbMapper.updateById(kb);
        return Result.success(kbMapper.selectById(id));
    }

    @Operation(summary = "删除知识库（同步删除 Dify）")
    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        KnowledgeBase kb = kbMapper.selectById(id);
        if (kb == null) {
            return Result.error("知识库不存在");
        }

        // 1. 同步删除 Dify 知识库
        if (kb.getKbId() != null && !kb.getKbId().startsWith("pending-")) {
            try {
                difySyncService.syncDelete(kb.getKbId());
            } catch (Exception e) {
                log.warn("[kb] 同步删除 Dify 知识库失败（SQL 仍继续）: kbId={}, err={}", kb.getKbId(), e.getMessage());
            }
        }

        // 2. 删除 MySQL 记录
        kbMapper.deleteById(id);
        return Result.success();
    }

    @Operation(summary = "启用/禁用知识库")
    @PutMapping("/{id}/status")
    public Result<Void> updateStatus(@PathVariable Long id, @RequestParam Integer status) {
        KnowledgeBase kb = kbMapper.selectById(id);
        if (kb == null) {
            return Result.error("知识库不存在");
        }
        kb.setStatus(status);
        kbMapper.updateById(kb);
        return Result.success();
    }

    @Operation(summary = "检查 Dify 知识库连通性")
    @GetMapping("/dify-status")
    public Result<Map<String, Object>> difyStatus() {
        return Result.success(difySyncService.checkStatus());
    }

    @Operation(summary = "上传文档到指定知识库")
    @PostMapping("/{id}/documents")
    public Result<KnowledgeBaseDocument> uploadDocument(@PathVariable Long id,
                                                         @RequestParam("file") MultipartFile file) {
        KnowledgeBase kb = kbMapper.selectById(id);
        if (kb == null) {
            return Result.error("知识库不存在");
        }
        if (file.isEmpty()) {
            return Result.error("上传文件为空");
        }

        String originalFilename = file.getOriginalFilename();
        String kbName = kb.getCategory();
        if (kbName == null || kbName.isBlank()) {
            kbName = kb.getName();
        }

        try {
            Map<String, Object> formParams = new HashMap<>();
            formParams.put("kb_name", kbName);
            formParams.put("indexing_technique", "high_quality");

            String resp = aiService.uploadFile(
                    "/knowledge-base/upload", "file", file.getBytes(), originalFilename, formParams);
            JSONObject json = JSONUtil.parseObj(resp);

            String documentId = json.getByPath("document_id", String.class);
            if (documentId == null || documentId.isBlank()) {
                documentId = json.getByPath("result.document.id", String.class);
            }
            if (documentId == null || documentId.isBlank()) {
                documentId = json.getByPath("result.id", String.class);
            }

            KnowledgeBaseDocument doc = new KnowledgeBaseDocument();
            doc.setKbId(id);
            doc.setName(originalFilename);
            doc.setFileType(file.getContentType());
            doc.setFileSize(file.getSize());
            doc.setDifyDocumentId(documentId);
            doc.setStatus(1);
            docMapper.insert(doc);

            // 更新知识库文档数量
            Long count = docMapper.selectCount(
                    new LambdaQueryWrapper<KnowledgeBaseDocument>().eq(KnowledgeBaseDocument::getKbId, id)
            );
            kb.setDocumentCount(count.intValue());
            kbMapper.updateById(kb);

            log.info("[kb-doc] 上传文档成功: kbId={}, name={}, difyDocId={}", id, originalFilename, documentId);
            return Result.success(doc);
        } catch (Exception e) {
            log.error("[kb-doc] 上传文档失败: kbId={}, name={}, err={}", id, originalFilename, e.getMessage());
            return Result.error("上传文档失败: " + e.getMessage());
        }
    }

    @Operation(summary = "查询知识库文档列表")
    @GetMapping("/{id}/documents")
    public Result<List<KnowledgeBaseDocument>> listDocuments(@PathVariable Long id) {
        KnowledgeBase kb = kbMapper.selectById(id);
        if (kb == null) {
            return Result.error("知识库不存在");
        }
        LambdaQueryWrapper<KnowledgeBaseDocument> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(KnowledgeBaseDocument::getKbId, id).orderByDesc(KnowledgeBaseDocument::getCreatedAt);
        return Result.success(docMapper.selectList(wrapper));
    }

    @Operation(summary = "删除知识库文档")
    @DeleteMapping("/documents/{docId}")
    public Result<Void> deleteDocument(@PathVariable Long docId) {
        KnowledgeBaseDocument doc = docMapper.selectById(docId);
        if (doc == null) {
            return Result.error("文档不存在");
        }
        KnowledgeBase kb = kbMapper.selectById(doc.getKbId());
        if (kb == null) {
            return Result.error("知识库不存在");
        }

        try {
            if (doc.getDifyDocumentId() != null && !doc.getDifyDocumentId().isBlank()) {
                String kbName = kb.getCategory();
                if (kbName == null || kbName.isBlank()) {
                    kbName = kb.getName();
                }
                aiService.delete("/knowledge-base/documents/" + doc.getDifyDocumentId()
                        + "?kb_name=" + java.net.URLEncoder.encode(kbName, "UTF-8"));
            }
        } catch (Exception e) {
            log.warn("[kb-doc] 同步删除 Dify 文档失败（继续删除本地记录）: docId={}, err={}", docId, e.getMessage());
        }

        docMapper.deleteById(docId);

        // 更新知识库文档数量
        Long count = docMapper.selectCount(
                new LambdaQueryWrapper<KnowledgeBaseDocument>().eq(KnowledgeBaseDocument::getKbId, kb.getId())
        );
        kb.setDocumentCount(count.intValue());
        kbMapper.updateById(kb);

        return Result.success();
    }
}
