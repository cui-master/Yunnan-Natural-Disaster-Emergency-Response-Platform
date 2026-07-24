package com.yunnan.emergency.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.yunnan.emergency.dto.KnowledgeUploadReq;
import com.yunnan.emergency.dto.KnowledgeVO;
import com.yunnan.emergency.entity.KnowledgeDoc;
import com.yunnan.emergency.mapper.KnowledgeMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class KnowledgeService {

    @Autowired
    private KnowledgeMapper knowledgeMapper;

    public List<KnowledgeVO> list(String category) {
        QueryWrapper<KnowledgeDoc> q = new QueryWrapper<>();
        if (category != null && !category.trim().isEmpty()) q.eq("category", category);
        q.orderByDesc("uploaded_at");
        return knowledgeMapper.selectList(q).stream().map(this::toVO).collect(Collectors.toList());
    }

    public KnowledgeVO upload(KnowledgeUploadReq req, String uploader) {
        KnowledgeDoc d = new KnowledgeDoc();
        d.setTitle(req.getTitle());
        d.setCategory(req.getCategory());
        d.setTagList(req.getTags() == null ? "" : String.join(",", req.getTags()));
        d.setDisasterList(req.getDisasterTypes() == null ? "" : String.join(",", req.getDisasterTypes()));
        d.setFileUrl(req.getFileUrl());
        d.setSource(req.getFileUrl());
        d.setChunkCount(0);
        d.setUploader(uploader);
        d.setUploadedAt(LocalDateTime.now());
        d.setUpdatedAt(LocalDateTime.now());
        knowledgeMapper.insert(d);
        return toVO(d);
    }

    public void delete(Long id) {
        knowledgeMapper.deleteById(id);
    }

    private KnowledgeVO toVO(KnowledgeDoc d) {
        KnowledgeVO v = new KnowledgeVO();
        v.setId(d.getId());
        v.setTitle(d.getTitle());
        v.setCategory(d.getCategory());
        v.setTags(split(d.getTagList()));
        v.setDisasterTypes(split(d.getDisasterList()));
        v.setChunkCount(d.getChunkCount());
        v.setSource(d.getSource());
        v.setUploader(d.getUploader());
        v.setUploadedAt(fmt(d.getUploadedAt()));
        v.setUpdatedAt(fmt(d.getUpdatedAt()));
        return v;
    }

    private List<String> split(String s) {
        if (s == null || s.trim().isEmpty()) return new ArrayList<>();
        return Arrays.stream(s.split(",")).filter(x -> !x.trim().isEmpty()).collect(Collectors.toList());
    }

    private String fmt(LocalDateTime t) {
        return t == null ? null : t.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
    }
}
