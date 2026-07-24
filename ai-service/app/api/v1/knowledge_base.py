from fastapi import APIRouter, UploadFile, File, Form, Query, HTTPException
from typing import Optional
from app.services import dify_dataset_service
from app.core.logging import logger

router = APIRouter(prefix="/knowledge-base", tags=["知识库管理"])


@router.post("/upload", summary="上传文件到知识库")
async def upload_to_knowledge_base(
    kb_name: str = Form(..., description="知识库名称：优化调度 / 风险评估"),
    file: UploadFile = File(..., description="支持 txt、pdf、docx、md 格式"),
    indexing_technique: str = Form("high_quality", description="索引方式：high_quality / economy"),
):
    """
    上传文件到指定的 Dify 知识库

    - **kb_name**: 知识库名称，可选值：`优化调度`、`风险评估`
    - **file**: 上传的文件，支持 txt、pdf、docx、md 格式
    - **indexing_technique**: 索引质量，high_quality（高质量）或 economy（经济模式）

    文件上传后 Dify 会异步进行解析、切片、向量化入库。
    """
    try:
        file_bytes = await file.read()
        filename = file.filename or "unnamed"

        if not filename:
            raise HTTPException(status_code=400, detail="文件名为空")

        result = await dify_dataset_service.upload_file(
            kb_name=kb_name,
            filename=filename,
            file_bytes=file_bytes,
            indexing_technique=indexing_technique,
        )

        document = result.get("document", result)
        document_id = document.get("id", "N/A") if isinstance(document, dict) else "N/A"

        return {
            "success": True,
            "message": f"文件 {filename} 成功提交至【{kb_name}】知识库，等待解析完成",
            "kb_name": kb_name,
            "filename": filename,
            "document_id": document_id,
            "result": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"上传文件到知识库失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/documents", summary="查询知识库文档列表")
async def list_kb_documents(
    kb_name: str = Query(..., description="知识库名称：优化调度 / 风险评估"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
):
    """
    查询指定知识库内的文档列表
    """
    try:
        result = await dify_dataset_service.list_documents(
            kb_name=kb_name,
            page=page,
            limit=limit,
            keyword=keyword,
        )
        return {
            "success": True,
            "kb_name": kb_name,
            "data": result,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"查询文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.delete("/documents/{document_id}", summary="删除知识库文档")
async def delete_kb_document(
    document_id: str,
    kb_name: str = Query(..., description="知识库名称：优化调度 / 风险评估"),
):
    """
    删除指定知识库中的文档

    **注意**：Dify API 不支持修改已有文档，更新文档时需先删除旧版本再重新上传。
    """
    try:
        success = await dify_dataset_service.delete_document(
            kb_name=kb_name,
            document_id=document_id,
        )
        if success:
            return {
                "success": True,
                "message": f"文档 {document_id} 已从【{kb_name}】知识库删除",
            }
        else:
            raise HTTPException(status_code=400, detail="删除失败，请检查文档ID是否正确")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/documents/{document_id}/status", summary="获取文档解析状态")
async def get_document_status(
    document_id: str,
    kb_name: str = Query(..., description="知识库名称：优化调度 / 风险评估"),
):
    """
    获取指定文档的解析状态

    文档上传后，Dify 会异步进行解析和向量化，可通过此接口查询进度。
    """
    try:
        doc = await dify_dataset_service.get_document_status(
            kb_name=kb_name,
            document_id=document_id,
        )
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        return {
            "success": True,
            "kb_name": kb_name,
            "document": doc,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询文档状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/upload-text", summary="通过文本创建知识库文档")
async def upload_text_to_kb(
    kb_name: str = Form(..., description="知识库名称：优化调度 / 风险评估"),
    name: str = Form(..., description="文档名称"),
    text: str = Form(..., description="文档内容"),
    indexing_technique: str = Form("high_quality", description="索引方式：high_quality / economy"),
):
    """
    直接通过文本内容创建知识库文档（无需上传文件）

    适用于程序化写入结构化数据到知识库的场景。
    """
    try:
        result = await dify_dataset_service.upload_text(
            kb_name=kb_name,
            name=name,
            text=text,
            indexing_technique=indexing_technique,
        )
        return {
            "success": True,
            "message": f"文本文档 {name} 已创建至【{kb_name}】知识库",
            "kb_name": kb_name,
            "result": result,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"创建文本文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/list", summary="获取可用知识库列表")
async def list_knowledge_bases():
    """
    获取系统配置的所有可用知识库名称及ID
    """
    kb_list = []
    for name, dataset_id in dify_dataset_service.kb_map.items():
        kb_list.append({
            "name": name,
            "dataset_id": dataset_id,
        })
    return {
        "success": True,
        "knowledge_bases": kb_list,
    }
