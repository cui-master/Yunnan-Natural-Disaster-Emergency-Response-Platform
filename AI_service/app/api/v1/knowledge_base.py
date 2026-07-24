from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.agents import dify_kb_client
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/knowledge-base", tags=["Dify 知识库"])

ALLOWED_EXT = {".txt", ".pdf", ".docx", ".md"}


@router.post("/upload", summary="上传文件到知识库")
async def upload_file(
    kb_name: str = Form(..., description="知识库名称：优化调度 / 风险评估"),
    file: UploadFile = File(..., description="支持 txt、pdf、docx、md"),
    indexing_technique: str = Form("high_quality"),
):
    """接收 Spring Boot 调用，上传文件到 Dify 指定知识库（异步解析、切片、入库）。"""
    name = file.filename or "unknown"
    ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型：{ext or '无后缀'}，仅支持 {', '.join(sorted(ALLOWED_EXT))}",
        )
    try:
        data = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取文件失败：{e}")

    try:
        result = await dify_kb_client.upload_file(
            kb_name=kb_name,
            filename=name,
            file_bytes=data,
            content_type=file.content_type or "application/octet-stream",
            indexing_technique=indexing_technique,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    logger.info(f"知识库上传提交成功: [{kb_name}] {name}")
    return {
        "success": True,
        "message": f"文件 {name} 成功提交至【{kb_name}】知识库，等待解析完成",
        "kb_name": kb_name,
        "filename": name,
        "result": result,
    }


@router.post("/upload-text", summary="通过文本创建文档")
async def upload_text(
    kb_name: str = Form(..., description="知识库名称：优化调度 / 风险评估"),
    name: str = Form(..., description="文档名称"),
    text: str = Form(..., description="文档内容"),
    indexing_technique: str = Form("high_quality"),
):
    try:
        result = await dify_kb_client.upload_text(kb_name, name, text, indexing_technique)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"success": True, "kb_name": kb_name, "result": result}


@router.get("/documents", summary="查询知识库文档列表")
async def list_documents(
    kb_name: str = Query(..., description="知识库名称"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
):
    try:
        result = await dify_kb_client.list_documents(kb_name, page, limit, keyword)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"success": True, "kb_name": kb_name, "data": result}


@router.get("/documents/{document_id}/status", summary="获取文档解析状态")
async def document_status(
    kb_name: str = Query(..., description="知识库名称"),
    document_id: str = ...,
):
    try:
        result = await dify_kb_client.document_status(kb_name, document_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"success": True, "kb_name": kb_name, "status": result}


@router.delete("/documents/{document_id}", summary="删除知识库文档")
async def delete_document(
    kb_name: str = Query(..., description="知识库名称"),
    document_id: str = ...,
):
    try:
        result = await dify_kb_client.delete_document(kb_name, document_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {
        "success": True,
        "message": f"文档 {document_id} 已从【{kb_name}】知识库删除",
        "result": result,
    }


@router.get("/list", summary="获取可用知识库列表")
async def list_knowledge_bases():
    return {
        "success": True,
        "knowledge_bases": [
            {"name": n, "dataset_id": d} for n, d in dify_kb_client.KB_MAP.items()
        ],
    }
