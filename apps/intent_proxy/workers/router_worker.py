import logging
from .base import BaseWorker
from kernel.compute.router import call_llm
from config import DEBUG_MODE

logger = logging.getLogger(__name__)

class RouterWorker(BaseWorker):
    """
    Role B 执行型工作者：转发路由。
    将请求发送给真正的模型，不包含 Orchestrator 的元指令。
    """
    async def run(self, messages: list, original_model: str = None, plan_intelligence: dict = None, **kwargs) -> dict:
        logger.info("👷 [Worker] 开始执行。正在加载架构师蓝图...")
        
        # 构建执行上下文
        execution_messages = messages.copy()
        
        if plan_intelligence and plan_intelligence.get("blueprint"):
            blueprint = plan_intelligence["blueprint"]
            # 将蓝图封装为系统指令，引导执行层
            directive_prompt = (
                "### [架构师指令 (Architect Blueprint)]\n"
                f"{blueprint}\n"
                "---\n"
                "请以此蓝图为核心导向，完成用户请求。"
            )
            execution_messages.insert(0, {"role": "system", "content": directive_prompt})
            logger.info("🎨 [Worker] 蓝图已注入执行流。")

        from config import ROUTER_CONFIG
        models_to_try = [original_model] if original_model and original_model in ROUTER_CONFIG else None
        
        response = await call_llm(
            messages=execution_messages,
            models_to_try=models_to_try,
            app_name="intent-proxy"
        )

        if DEBUG_MODE:
            content = response["choices"][0]["message"]["content"]
            border = "·" * 90
            print(f"\n{border}")
            print("👷 [ROLE B: WORKER EXECUTION RESULT]")
            print(f"{border}")
            for line in content.split('\n'):
                print(f"  ┃ {line}")
            print(f"{border}\n")

        return response

