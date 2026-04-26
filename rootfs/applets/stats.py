from kernel.telemetry import global_telemetry
from rootfs.applets.base import BaseApplet

class StatsApplet(BaseApplet):
    @property
    def name(self) -> str:
        return "stats"

    @property
    def description(self) -> str:
        return "View transient OS Telemetry stats"

    async def run(self, args: list[str]) -> None:
        stats = global_telemetry.get_all_model_stats()
        print("\n📊 --- Telemetry Stats (Transient OS Level) ---")
        if not stats:
            print("没有 Telemetry 数据记录。试着运行一次 App 或者拉起 API 接受请求。")
        else:
            for m, s in stats.items():
                print(f"Model: {m} | Calls: {s.total_calls} | Tokens: {s.total_tokens} | Cost: ${s.total_cost:.4f} | Health: {'🟢' if s.is_healthy else '🔴'} ({s.success_rate*100:.1f}%) | Avg Latency: {s.avg_latency_ms:.0f}ms")
        print("----------------------------------------------")
