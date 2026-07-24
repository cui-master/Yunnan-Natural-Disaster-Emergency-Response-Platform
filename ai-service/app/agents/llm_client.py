"""统一 LLM 客户端 —— 支持 DeepSeek / 通义千问动态切换

作为 Dify 工作流失败时的 LLM 降级方案。
- DeepSeek V4 推理模型：会产生 reasoning_content，只取 content 返回
- 通义千问：OpenAI 兼容协议

provider 可通过 admin 接口运行时动态修改，即时影响降级行为。
"""
import httpx
from typing import Optional
from app.core.config import settings
from app.core.logging import logger


class LLMClient:
    """统一 LLM 客户端"""

    def __init__(self):
        self._provider: str = settings.LLM_PROVIDER
        # 运行时可覆盖的配置（admin 接口动态修改）
        self._overrides: dict = {}

    # ────────── 配置管理 ──────────

    def _get_config(self, provider: Optional[str] = None) -> dict:
        """获取指定 provider 的配置（含运行时覆盖）"""
        provider = provider or self._provider
        override = self._overrides.get(provider, {})

        if provider == "deepseek":
            return {
                "api_key": override.get("api_key", settings.DEEPSEEK_API_KEY),
                "api_base": override.get("api_base", settings.DEEPSEEK_API_BASE),
                "model": override.get("model", settings.DEEPSEEK_MODEL),
            }
        elif provider == "qwen":
            return {
                "api_key": override.get("api_key", settings.QWEN_API_KEY),
                "api_base": override.get("api_base", settings.QWEN_API_BASE),
                "model": override.get("model", settings.QWEN_MODEL),
            }
        raise ValueError(f"不支持的 LLM provider: {provider}（仅支持 deepseek / qwen）")

    def set_provider(self, provider: str) -> None:
        """动态切换 provider"""
        if provider not in ("deepseek", "qwen"):
            raise ValueError(f"不支持的 LLM provider: {provider}")
        self._provider = provider
        logger.info(f"LLM provider 已切换为: {provider}")

    def update_config(self, provider: str, api_key: Optional[str] = None,
                      api_base: Optional[str] = None, model: Optional[str] = None) -> None:
        """动态更新某 provider 的配置"""
        if provider not in ("deepseek", "qwen"):
            raise ValueError(f"不支持的 LLM provider: {provider}")
        cfg = self._overrides.setdefault(provider, {})
        if api_key is not None:
            cfg["api_key"] = api_key
        if api_base is not None:
            cfg["api_base"] = api_base
        if model is not None:
            cfg["model"] = model
        logger.info(f"LLM 配置已更新: provider={provider}, model={model or '未变'}")

    def get_config(self) -> dict:
        """获取当前配置（api_key 脱敏）"""
        cfg = self._get_config()
        api_key = cfg["api_key"]
        masked = api_key[:8] + "***" + api_key[-4:] if len(api_key) > 12 else "***"
        return {
            "provider": self._provider,
            "api_base": cfg["api_base"],
            "model": cfg["model"],
            "api_key_masked": masked,
        }

    # ────────── 核心调用 ──────────

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        provider: Optional[str] = None,
    ) -> str:
        """调用 LLM 生成文本

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户输入
            temperature: 温度
            max_tokens: 最大生成 token 数
            provider: 指定 provider（默认用当前 provider）

        Returns:
            LLM 生成的文本

        Raises:
            RuntimeError: 调用失败
        """
        cfg = self._get_config(provider)
        url = f"{cfg['api_base'].rstrip('/')}/chat/completions"

        headers = {
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": cfg["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

                choices = data.get("choices", [])
                if not choices:
                    raise RuntimeError("LLM 返回空 choices")

                message = choices[0].get("message", {})
                content = message.get("content", "")

                # DeepSeek V4 的 reasoning_content：推理过程，正常不返回给用户
                reasoning = message.get("reasoning_content")
                if reasoning:
                    logger.debug(
                        f"[LLM:{cfg['model']}] reasoning_content 长度={len(reasoning)}"
                    )

                # 兜底：推理模型可能把所有内容放在 reasoning_content，content 为空
                if not content and reasoning:
                    logger.warning(
                        f"[LLM:{cfg['model']}] content 为空，使用 reasoning_content 兜底"
                    )
                    content = reasoning

                if not content:
                    raise RuntimeError("LLM 返回空 content（content 和 reasoning_content 均为空）")

                logger.info(
                    f"[LLM:{cfg['model']}] 生成成功，长度={len(content)}"
                )
                return content

        except httpx.HTTPStatusError as e:
            logger.error(
                f"LLM HTTP 错误: {e.response.status_code} - {e.response.text[:300]}"
            )
            raise RuntimeError(f"LLM 调用失败 ({e.response.status_code}): {e.response.text[:200]}")
        except httpx.RequestError as e:
            logger.error(f"LLM 连接失败: {e}")
            raise RuntimeError(f"LLM 连接失败: {str(e)}")

    async def test_connectivity(self, provider: Optional[str] = None) -> dict:
        """测试 LLM 连通性"""
        cfg = self._get_config(provider)
        try:
            result = await self.chat(
                system_prompt="你是一个测试助手。",
                user_prompt="请回复：连接成功",
                max_tokens=200,
                provider=provider,
            )
            return {
                "success": True,
                "provider": provider or self._provider,
                "model": cfg["model"],
                "response": result[:100],
            }
        except Exception as e:
            return {
                "success": False,
                "provider": provider or self._provider,
                "model": cfg["model"],
                "error": str(e),
            }


llm_client = LLMClient()
