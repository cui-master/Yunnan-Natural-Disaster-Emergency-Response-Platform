package com.yunnan.emergency.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import cn.hutool.core.io.FileUtil;
import cn.hutool.core.util.IdUtil;
import com.yunnan.emergency.common.Result;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

@Tag(name = "文件上传", description = "图片、文档等文件上传")
@RestController
@RequestMapping("/upload")
public class FileUploadController {

    private static final Logger log = LoggerFactory.getLogger(FileUploadController.class);

    @Value("${file.upload-path}")
    private String uploadPath;

    @Value("${file.url-prefix}")
    private String urlPrefix;

    /** 允许上传的图片扩展名白名单（小写） */
    private static final Set<String> IMAGE_EXTENSIONS = Set.of(
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"
    );

    /** 允许上传的文档扩展名白名单（小写） */
    private static final Set<String> DOCUMENT_EXTENSIONS = Set.of(
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".txt", ".csv", ".md", ".json", ".xml"
    );

    @Operation(summary = "上传单张图片")
    @PostMapping("/image")
    public Result<Map<String, String>> uploadImage(@RequestParam("file") MultipartFile file) throws IOException {
        if (file.isEmpty()) {
            return Result.error("文件不能为空");
        }

        String originalFilename = file.getOriginalFilename();
        String ext = extractExtension(originalFilename);
        if (!IMAGE_EXTENSIONS.contains(ext.toLowerCase())) {
            log.warn("[upload] 拒绝非白名单图片上传: originalFilename={}, ext={}", originalFilename, ext);
            return Result.error("不支持的图片格式，允许: " + IMAGE_EXTENSIONS);
        }

        String fileName = IdUtil.simpleUUID() + ext;
        File destFile = safeDestFile(uploadPath + "/images", fileName);

        file.transferTo(destFile);

        Map<String, String> result = new HashMap<>();
        result.put("fileName", fileName);
        result.put("url", urlPrefix + "/images/" + fileName);
        result.put("originalName", originalFilename);

        return Result.success(result);
    }

    @Operation(summary = "上传多张图片")
    @PostMapping("/images")
    public Result<List<Map<String, String>>> uploadImages(@RequestParam("files") MultipartFile[] files) throws IOException {
        List<Map<String, String>> results = new ArrayList<>();
        for (MultipartFile file : files) {
            if (!file.isEmpty()) {
                Result<Map<String, String>> result = uploadImage(file);
                if (result.getCode() == 200 && result.getData() != null) {
                    results.add(result.getData());
                }
            }
        }
        return Result.success(results);
    }

    @Operation(summary = "上传文档")
    @PostMapping("/document")
    public Result<Map<String, String>> uploadDocument(@RequestParam("file") MultipartFile file) throws IOException {
        if (file.isEmpty()) {
            return Result.error("文件不能为空");
        }

        String originalFilename = file.getOriginalFilename();
        String ext = extractExtension(originalFilename);
        if (!DOCUMENT_EXTENSIONS.contains(ext.toLowerCase())) {
            log.warn("[upload] 拒绝非白名单文档上传: originalFilename={}, ext={}", originalFilename, ext);
            return Result.error("不支持的文档格式，允许: " + DOCUMENT_EXTENSIONS);
        }

        String fileName = IdUtil.simpleUUID() + ext;
        File destFile = safeDestFile(uploadPath + "/documents", fileName);

        file.transferTo(destFile);

        Map<String, String> result = new HashMap<>();
        result.put("fileName", fileName);
        result.put("url", urlPrefix + "/documents/" + fileName);
        result.put("originalName", originalFilename);
        result.put("size", String.valueOf(file.getSize()));

        return Result.success(result);
    }

    // ============ 安全工具方法 ============

    /**
     * 提取文件扩展名（含点号），无扩展名时返回空字符串
     */
    private static String extractExtension(String filename) {
        if (filename == null || filename.isEmpty()) {
            return "";
        }
        int dotIndex = filename.lastIndexOf(".");
        if (dotIndex < 0 || dotIndex == filename.length() - 1) {
            return "";
        }
        return filename.substring(dotIndex).toLowerCase();
    }

    /**
     * 安全地创建目标文件，防止路径遍历攻击
     * 校验最终路径以 baseDir 为前缀，拒绝 "../" 等目录穿越
     */
    private static File safeDestFile(String baseDir, String fileName) {
        File destDir = new File(baseDir);
        if (!destDir.exists()) {
            destDir.mkdirs();
        }
        File destFile = new File(destDir, fileName);

        // 路径遍历防护：确保目标文件在预期目录内
        String canonicalBase;
        String canonicalDest;
        try {
            canonicalBase = destDir.getCanonicalPath();
            canonicalDest = destFile.getCanonicalPath();
        } catch (IOException e) {
            throw new IllegalArgumentException("非法文件路径: " + fileName);
        }
        if (!canonicalDest.startsWith(canonicalBase + File.separator)) {
            throw new IllegalArgumentException("检测到路径遍历攻击，拒绝文件: " + fileName);
        }

        return destFile;
    }
}
