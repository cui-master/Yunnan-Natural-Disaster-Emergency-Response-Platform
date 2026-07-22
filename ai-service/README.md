# AI 服务（FastAPI，MVP 桩）

提供 `/api/plan/generate` 接收事件上下文，返回结构化应急处置方案（步骤、资源建议、引用来源）。
当前为**可替换桩**：将 `main.py` 的 `build_plan()` 内部替换为 LangChain / LlamaIndex 真实调用即可，接口契约不变。

## 本地运行
```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --port 8000
```
文档：http://localhost:8000/docs
