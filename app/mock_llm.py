from __future__ import annotations

import random
import time
from dataclasses import dataclass

from .incidents import STATE


@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class FakeResponse:
    text: str
    usage: FakeUsage
    model: str
    ttft_ms: int


class FakeLLM:
    def __init__(self, model: str = "fake-llm") -> None:
        self.model = model

    def generate(self, prompt: str) -> FakeResponse:
        started = time.perf_counter()
        time.sleep(0.05)  # mô phỏng thời điểm token đầu tiên sẵn sàng
        ttft_ms = int((time.perf_counter() - started) * 1000)
        time.sleep(0.10)
        input_tokens = max(20, len(prompt) // 4)
        output_tokens = random.randint(80, 180)
        if STATE["cost_spike"]:
            output_tokens *= 4
        lowered = prompt.lower()
        if "metrics detect incidents" in lowered:
            answer = (
                "Metrics phát hiện triệu chứng và thời điểm sự cố. Logs xác định request bị ảnh hưởng "
                "qua correlation ID. Traces chỉ ra span retrieval hoặc generation gây chậm/lỗi; "
                "từ đó kết luận root cause bằng bằng chứng cùng request."
            )
        elif "refunds are available" in lowered:
            answer = "Theo tài liệu mẫu, hoàn tiền trong 7 ngày khi có bằng chứng mua hàng."
        elif "do not expose pii" in lowered:
            answer = "Không ghi PII thô vào logs hoặc traces; chỉ lưu bản tóm tắt đã che thông tin nhạy cảm."
        else:
            answer = "Không tìm thấy tài liệu chuyên ngành phù hợp. Hãy kiểm tra nguồn dữ liệu trước khi kết luận."
        return FakeResponse(
            text=answer,
            usage=FakeUsage(input_tokens, output_tokens),
            model=self.model,
            ttft_ms=ttft_ms,
        )
