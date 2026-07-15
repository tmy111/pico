<<<<<<< HEAD
﻿"""妯″瀷鍚庣閫傞厤灞傘€?

runtime 鍙叧蹇冧竴浠朵簨锛氱粰鎴戜竴涓?prompt锛屾垜鎷垮洖涓€娈垫枃鏈€?
涓嶅悓 provider 鍦?HTTP 鎺ュ彛銆佸搷搴旂粨鏋勩€佹槸鍚︽敮鎸?prompt cache 涓婇兘鏈夊樊寮傦紝
杩欎簺宸紓閮藉湪杩欓噷琚姽骞虫垚缁熶竴鐨?complete() 鎺ュ彛銆?
=======
"""模型后端适配层。

runtime 只关心一件事：给我一个 prompt，我拿回一段文本。
不同 provider 在 HTTP 接口、响应结构、是否支持 prompt cache 上都有差异，
这些差异都在这里被抹平成统一的 complete() 接口。
>>>>>>> origin/main
"""

import json
import time
from http.client import RemoteDisconnected
import urllib.error
import urllib.request

OPENAI_COMPATIBLE_USER_AGENT = "pico/0.1"


<<<<<<< HEAD
# 娴嬭瘯鐢ㄥ亣妯″瀷锛氭寜棰勮椤哄簭杩斿洖鏂囨湰锛屼笉鍙戠湡瀹炵綉缁滆姹傘€?
=======
# 测试用假模型：按预设顺序返回文本，不发真实网络请求。
>>>>>>> origin/main
class FakeModelClient:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.prompts = []
        self.supports_prompt_cache = False
        self.last_completion_metadata = {}

    def complete(self, prompt, max_new_tokens, **kwargs):
        self.prompts.append(prompt)
        if not getattr(self, "last_completion_metadata", None):
            self.last_completion_metadata = {}
        if not self.outputs:
            raise RuntimeError("fake model ran out of outputs")
        return self.outputs.pop(0)


<<<<<<< HEAD
# Ollama 鍚庣锛氳皟鐢ㄦ湰鏈?Ollama /api/generate 鎺ュ彛銆?
=======
# Ollama 后端：调用本机 Ollama /api/generate 接口。
>>>>>>> origin/main
class OllamaModelClient:
    def __init__(self, model, host, temperature, top_p, timeout):
        self.model = model
        self.host = host.rstrip("/")
        self.temperature = temperature
        self.top_p = top_p
        self.timeout = timeout
        self.supports_prompt_cache = False
        self.last_completion_metadata = {}

    def complete(self, prompt, max_new_tokens, **kwargs):
<<<<<<< HEAD
        # Ollama 褰撳墠涓嶆敮鎸佹垜浠繖閲屾帴鍏ョ殑 prompt cache 璇箟锛?
        # 鎵€浠?runtime 浼犱笅鏉ョ殑缂撳瓨鍙傛暟浼氳蹇界暐銆?
=======
        # Ollama 当前不支持我们这里接入的 prompt cache 语义，
        # 所以 runtime 传下来的缓存参数会被忽略。
>>>>>>> origin/main
        self.last_completion_metadata = {}
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "raw": False,
            "think": False,
            "options": {
                "num_predict": max_new_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
            },
        }
        request = urllib.request.Request(
            self.host + "/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama request failed with HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Could not reach Ollama.\n"
                "Make sure `ollama serve` is running and the model is available.\n"
                f"Host: {self.host}\n"
                f"Model: {self.model}"
            ) from exc

        if data.get("error"):
            raise RuntimeError(f"Ollama error: {data['error']}")
        return data.get("response", "")


<<<<<<< HEAD
# 缁熶竴琛ラ綈 OpenAI-compatible base URL 鐨?/v1 鍚庣紑銆?
=======
# 统一补齐 OpenAI-compatible base URL 的 /v1 后缀。
>>>>>>> origin/main
def _normalize_versioned_base_url(base_url):
    base = str(base_url).rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    return base


<<<<<<< HEAD
# 浠?OpenAI-compatible 鏅€?JSON 鍝嶅簲閲屾娊鍙栨枃鏈€?
=======
# 从 OpenAI-compatible 普通 JSON 响应里抽取文本。
>>>>>>> origin/main
def _extract_openai_text(data):
    if data.get("output_text"):
        return data["output_text"]

    for item in data.get("output", []):
        for content in item.get("content", []):
            if isinstance(content, dict):
                text = content.get("text")
                if text:
                    return text

    choices = data.get("choices", [])
    if choices:
        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        return text

    return ""


<<<<<<< HEAD
# 浠?OpenAI-compatible SSE 娴佸紡鏂囨湰閲屾娊鍙栨渶缁堟枃鏈€?
=======
# 从 OpenAI-compatible SSE 流式文本里抽取最终文本。
>>>>>>> origin/main
def _extract_openai_text_from_sse(body_text):
    last_response = None
    deltas = []
    for line in body_text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[len("data:"):].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue
        event_type = event.get("type", "")
        if event_type == "response.output_text.delta":
            delta = event.get("delta")
            if isinstance(delta, str):
                deltas.append(delta)
            continue
        if event_type == "response.output_text.done":
            text = event.get("text")
            if isinstance(text, str) and text:
                return text
        part = event.get("part")
        if isinstance(part, dict):
            text = part.get("text")
            if isinstance(text, str) and text:
                return text
        item = event.get("item")
        if isinstance(item, dict):
            text = _extract_openai_text({"output": [item]})
            if text:
                return text
        response = event.get("response")
        if isinstance(response, dict):
            last_response = response
            text = _extract_openai_text(response)
            if text:
                return text
        text = _extract_openai_text(event)
        if text:
            return text
    if deltas:
        return "".join(deltas)
    if isinstance(last_response, dict):
        return _extract_openai_text(last_response)
    return ""


<<<<<<< HEAD
# 浠?SSE 鍝嶅簲閲屽悓鏃舵娊鍙栨枃鏈拰瀹屾暣 response 鍏冩暟鎹€?
=======
# 从 SSE 响应里同时抽取文本和完整 response 元数据。
>>>>>>> origin/main
def _extract_openai_response_from_sse(body_text):
    last_response = None
    deltas = []
    for line in body_text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[len("data:"):].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue
        response = event.get("response")
        if isinstance(response, dict):
            last_response = response
            if event.get("type") == "response.completed":
                text = _extract_openai_text(response)
                if text:
                    return text, response
        event_type = event.get("type", "")
        if event_type == "response.output_text.delta":
            delta = event.get("delta")
            if isinstance(delta, str):
                deltas.append(delta)
        elif event_type == "response.output_text.done":
            text = event.get("text")
            if isinstance(text, str) and text:
                return text, last_response or {}
        else:
            text = _extract_openai_text(event)
            if text:
                return text, event
    if deltas:
        return "".join(deltas), last_response or {}
    if isinstance(last_response, dict):
        return _extract_openai_text(last_response), last_response
    return "", {}


<<<<<<< HEAD
# 鏁寸悊 usage/cache 缁熻瀛楁銆?
def _extract_usage_cache_details(data):
    # 鎶婁笉鍚?OpenAI-compatible 杩斿洖閲岀殑 usage 瀛楁鏁寸悊鎴愮粺涓€缁撴瀯锛?
    # 璁?runtime/trace/report 涓嶉渶瑕佸叧蹇?provider 缁嗚妭銆?
=======
# 整理 usage/cache 统计字段。
def _extract_usage_cache_details(data):
    # 把不同 OpenAI-compatible 返回里的 usage 字段整理成统一结构，
    # 让 runtime/trace/report 不需要关心 provider 细节。
>>>>>>> origin/main
    usage = data.get("usage") or {}
    input_tokens = usage.get("input_tokens", usage.get("prompt_tokens"))
    output_tokens = usage.get("output_tokens", usage.get("completion_tokens"))
    input_details = usage.get("input_tokens_details") or usage.get("prompt_tokens_details") or {}
    cached_tokens = int(input_details.get("cached_tokens") or 0)
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": usage.get("total_tokens"),
        "cached_tokens": cached_tokens,
        "cache_hit": cached_tokens > 0,
    }


<<<<<<< HEAD
# OpenAI-compatible 鍚庣锛氳皟鐢?/responses 鎺ュ彛銆?
=======
# OpenAI-compatible 后端：调用 /responses 接口。
>>>>>>> origin/main
class OpenAICompatibleModelClient:
    def __init__(self, model, base_url, api_key, temperature, timeout):
        self.model = model
        self.base_url = _normalize_versioned_base_url(base_url)
        self.api_key = api_key
        self.temperature = temperature
        self.timeout = timeout
<<<<<<< HEAD
        # 褰撳墠鍙湪鏄庣‘鏀寔 prompt cache 璇箟鐨勫悗绔笂鍚敤杩欐潯閾捐矾锛?
        # 閬垮厤瀵逛笉鏀寔鐨勫悗绔紶涓€涓€滅湅璧锋潵缁熶竴銆佸叾瀹炴病鎰忎箟鈥濈殑浼弬鏁般€?
=======
        # 当前只在明确支持 prompt cache 语义的后端上启用这条链路，
        # 避免对不支持的后端传一个“看起来统一、其实没意义”的伪参数。
>>>>>>> origin/main
        self.supports_prompt_cache = any(host in self.base_url for host in ("openai.com", "right.codes"))
        self.last_completion_metadata = {}

    def complete(self, prompt, max_new_tokens, prompt_cache_key=None, prompt_cache_retention=None):
<<<<<<< HEAD
        """鍚?OpenAI-compatible `/responses` 鎺ュ彛鍙戣捣涓€娆℃ā鍨嬭皟鐢ㄣ€?

        涓轰粈涔堝瓨鍦細
        runtime 涓嶅簲璇ョ煡閬?HTTP 缁嗚妭銆丼SE 缁嗚妭銆乽sage 瀛楁闀夸粈涔堟牱锛?
        鏇翠笉搴旇鑷繁鍘诲垽鏂?prompt cache 鍙傛暟瑕佷笉瑕佸甫銆傝繖涓嚱鏁版妸杩欎簺鍚庣
        缁嗚妭閮藉寘璧锋潵锛屽涓婂眰鏆撮湶缁熶竴鐨?`complete()` 琛屼负銆?

        杈撳叆 / 杈撳嚭锛?
        - 杈撳叆锛氬畬鏁?prompt銆佹渶澶ц緭鍑?token锛屼互鍙婂彲閫夌殑 prompt cache 鍙傛暟
        - 杈撳嚭锛氭ā鍨嬫渶缁堟枃鏈紱鍚屾椂鎶?usage / cached_tokens 绛夊厓鏁版嵁鍐欒繘
          `self.last_completion_metadata`

        鍦?agent 閾捐矾閲岀殑浣嶇疆锛?
        瀹冧綅浜?`Pico.ask()` 鐨勬ā鍨嬭皟鐢ㄩ樁娈碉紝鏄ǔ瀹氬墠缂€缂撳瓨澶嶇敤閾捐矾鐪熸
        钀藉埌 provider API 鐨勫湴鏂广€?
=======
        """向 OpenAI-compatible `/responses` 接口发起一次模型调用。

        为什么存在：
        runtime 不应该知道 HTTP 细节、SSE 细节、usage 字段长什么样，
        更不应该自己去判断 prompt cache 参数要不要带。这个函数把这些后端
        细节都包起来，对上层暴露统一的 `complete()` 行为。

        输入 / 输出：
        - 输入：完整 prompt、最大输出 token，以及可选的 prompt cache 参数
        - 输出：模型最终文本；同时把 usage / cached_tokens 等元数据写进
          `self.last_completion_metadata`

        在 agent 链路里的位置：
        它位于 `Pico.ask()` 的模型调用阶段，是稳定前缀缓存复用链路真正
        落到 provider API 的地方。
>>>>>>> origin/main
        """
        self.last_completion_metadata = {}
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        }
                    ],
                }
            ],
            "max_output_tokens": max_new_tokens,
            "stream": False,
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature
<<<<<<< HEAD
        # runtime 浼犲叆鐨勬槸鈥滅ǔ瀹氬墠缂€鈥濈殑绛惧悕锛岃€屼笉鏄暣娈?prompt 鐨勭鍚嶃€?
        # 杩欐牱缂撳瓨澶嶇敤閽堝鐨勬槸绋冲畾娈碉紝涓嶄細鍥犱负鍔ㄦ€?history 姣忚疆鍙樺寲鑰屽け鏁堛€?
=======
        # runtime 传入的是“稳定前缀”的签名，而不是整段 prompt 的签名。
        # 这样缓存复用针对的是稳定段，不会因为动态 history 每轮变化而失效。
>>>>>>> origin/main
        if self.supports_prompt_cache and prompt_cache_key:
            payload["prompt_cache_key"] = prompt_cache_key
        if self.supports_prompt_cache and prompt_cache_retention:
            payload["prompt_cache_retention"] = prompt_cache_retention

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": OPENAI_COMPATIBLE_USER_AGENT,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = urllib.request.Request(
            self.base_url + "/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        attempts = 3
        for attempt in range(attempts):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    body_text = response.read().decode("utf-8")
                    headers = getattr(response, "headers", {}) or {}
                    content_type = headers.get("Content-Type", "")
                break
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                if exc.code >= 500 and attempt < attempts - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise RuntimeError(f"OpenAI-compatible request failed with HTTP {exc.code}: {body}") from exc
            except (urllib.error.URLError, RemoteDisconnected) as exc:
                if attempt < attempts - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise RuntimeError(
                    "Could not reach the OpenAI-compatible backend.\n"
                    f"Base URL: {self.base_url}\n"
                    f"Model: {self.model}"
                ) from exc

<<<<<<< HEAD
        # 鏈変簺鍏煎鍚庣杩斿洖鏅€?JSON锛屾湁浜涜繑鍥?SSE銆?
        # 杩欓噷涓ょ閮芥帴浣忥紝骞跺敖閲忕粺涓€鎶藉彇鏂囨湰鍜?usage/cache 鍏冩暟鎹€?
        if content_type.startswith("text/event-stream") or body_text.lstrip().startswith("data:"):
            text, response_data = _extract_openai_response_from_sse(body_text)
            if isinstance(response_data, dict) and response_data:
                # 杩欎簺鍏冩暟鎹細涓€璺紶鍥?runtime锛岃繘鍏?trace 鍜?report锛?
                # 鐢ㄦ潵瑙傚療 prompt cache 鏄惁鐪熺殑鍛戒腑銆?
=======
        # 有些兼容后端返回普通 JSON，有些返回 SSE。
        # 这里两种都接住，并尽量统一抽取文本和 usage/cache 元数据。
        if content_type.startswith("text/event-stream") or body_text.lstrip().startswith("data:"):
            text, response_data = _extract_openai_response_from_sse(body_text)
            if isinstance(response_data, dict) and response_data:
                # 这些元数据会一路传回 runtime，进入 trace 和 report，
                # 用来观察 prompt cache 是否真的命中。
>>>>>>> origin/main
                self.last_completion_metadata = {
                    "prompt_cache_supported": self.supports_prompt_cache,
                    "prompt_cache_key": prompt_cache_key,
                    "prompt_cache_retention": prompt_cache_retention,
                    **_extract_usage_cache_details(response_data),
                }
            if text:
                return text
            raise RuntimeError("OpenAI-compatible error: could not extract text from event stream response")

        try:
            data = json.loads(body_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "OpenAI-compatible error: backend returned non-JSON content that could not be parsed"
            ) from exc
        if data.get("error"):
            raise RuntimeError(f"OpenAI-compatible error: {data['error']}")
        self.last_completion_metadata = {
            "prompt_cache_supported": self.supports_prompt_cache,
            "prompt_cache_key": prompt_cache_key,
            "prompt_cache_retention": prompt_cache_retention,
            **_extract_usage_cache_details(data),
        }
        return _extract_openai_text(data)


<<<<<<< HEAD
# 浠?DeepSeek 鍝嶅簲閲屾娊鍙栫涓€娈垫枃鏈€?
def _extract_deepseek_content_text(content):
    if isinstance(content, str) and content.strip():
        return content
    if isinstance(content, list):
        for item in content:
            if isinstance(item, str) and item.strip():
                return item
            if not isinstance(item, dict):
                continue
            for key in ("text", "content", "output_text"):
                text = _extract_deepseek_content_text(item.get(key))
                if text:
                    return text
    if isinstance(content, dict):
        for key in ("text", "content", "output_text"):
            text = _extract_deepseek_content_text(content.get(key))
            if text:
=======
# 从 Anthropic-compatible 响应里抽取第一段文本。
def _extract_anthropic_text(data):
    for item in data.get("content", []):
        if isinstance(item, dict) and item.get("type") == "text":
            text = item.get("text")
            if isinstance(text, str) and text:
>>>>>>> origin/main
                return text
    return ""


<<<<<<< HEAD
def _extract_deepseek_text(data):
    for key in ("content", "completion", "text", "response", "output_text"):
        text = _extract_deepseek_content_text(data.get(key))
        if text:
            return text

    choices = data.get("choices", [])
    if isinstance(choices, list):
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            for key in ("message", "delta"):
                message = choice.get(key)
                if isinstance(message, dict):
                    for message_key in ("content", "text", "output_text"):
                        text = _extract_deepseek_content_text(message.get(message_key))
                        if text:
                            return text
            for key in ("content", "text"):
                text = _extract_deepseek_content_text(choice.get(key))
                if text:
                    return text
    return ""


def _has_deepseek_reasoning_only(data):
    choices = data.get("choices", [])
    if not isinstance(choices, list):
        return bool(data.get("reasoning_content"))
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message")
        if isinstance(message, dict) and _extract_deepseek_content_text(message.get("reasoning_content")):
            return True
        delta = choice.get("delta")
        if isinstance(delta, dict) and _extract_deepseek_content_text(delta.get("reasoning_content")):
            return True
    return False


# DeepSeek backend response shape helper.
def _summarize_response_shape(value, depth=0):
    if depth >= 2:
        return type(value).__name__
    if isinstance(value, dict):
        parts = []
        for key in sorted(value)[:8]:
            parts.append(f"{key}: {_summarize_response_shape(value[key], depth + 1)}")
        extra = ", ..." if len(value) > 8 else ""
        return "{" + ", ".join(parts) + extra + "}"
    if isinstance(value, list):
        if not value:
            return "[]"
        return f"[{_summarize_response_shape(value[0], depth + 1)} x{len(value)}]"
    if isinstance(value, str):
        return f"str({len(value)})"
    return type(value).__name__


class DeepSeekModelClient:
=======
# Anthropic-compatible 后端：调用 /messages 接口。
class AnthropicCompatibleModelClient:
>>>>>>> origin/main
    def __init__(self, model, base_url, api_key, temperature, timeout):
        self.model = model
        self.base_url = _normalize_versioned_base_url(base_url)
        self.api_key = api_key
        self.temperature = temperature
        self.timeout = timeout
        self.supports_prompt_cache = False
        self.last_completion_metadata = {}

    def complete(self, prompt, max_new_tokens, prompt_cache_key=None, prompt_cache_retention=None):
<<<<<<< HEAD
        # 涓轰簡淇濇寔缁熶竴鎺ュ彛锛宺untime 浠嶇劧浼氫紶缂撳瓨鍙傛暟杩涙潵锛?
        # 杩欓噷鍙槸鏄惧紡涓㈠純锛屽洜涓哄綋鍓?DeepSeek 璺緞娌℃湁鎺ョ紦瀛樺鐢ㄣ€?
=======
        # 为了保持统一接口，runtime 仍然会传缓存参数进来；
        # 这里只是显式丢弃，因为当前 Anthropic-compatible 路径没有接缓存复用。
>>>>>>> origin/main
        del prompt_cache_key, prompt_cache_retention
        self.last_completion_metadata = {}
        payload = {
            "model": self.model,
<<<<<<< HEAD
            "messages": [{"role": "user", "content": prompt}],
=======
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        }
                    ],
                }
            ],
>>>>>>> origin/main
            "max_tokens": max_new_tokens,
            "stream": False,
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature

        headers = {
            "Content-Type": "application/json",
<<<<<<< HEAD
            "Accept": "application/json",
            "User-Agent": OPENAI_COMPATIBLE_USER_AGENT,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = urllib.request.Request(
            self.base_url + "/chat/completions",
=======
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        request = urllib.request.Request(
            self.base_url + "/messages",
>>>>>>> origin/main
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        attempts = 3
        for attempt in range(attempts):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    body_text = response.read().decode("utf-8")
                break
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                if exc.code >= 500 and attempt < attempts - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
<<<<<<< HEAD
                raise RuntimeError(f"DeepSeek request failed with HTTP {exc.code}: {body}") from exc
=======
                raise RuntimeError(f"Anthropic-compatible request failed with HTTP {exc.code}: {body}") from exc
>>>>>>> origin/main
            except (urllib.error.URLError, RemoteDisconnected) as exc:
                if attempt < attempts - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise RuntimeError(
<<<<<<< HEAD
                    "Could not reach the DeepSeek backend.\n"
=======
                    "Could not reach the Anthropic-compatible backend.\n"
>>>>>>> origin/main
                    f"Base URL: {self.base_url}\n"
                    f"Model: {self.model}"
                ) from exc

        try:
            data = json.loads(body_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
<<<<<<< HEAD
                "DeepSeek error: backend returned non-JSON content that could not be parsed"
            ) from exc
        if data.get("error"):
            raise RuntimeError(f"DeepSeek error: {data['error']}")
        self.last_completion_metadata = {
            "prompt_cache_supported": self.supports_prompt_cache,
            **_extract_usage_cache_details(data),
        }
        text = _extract_deepseek_text(data)
        if text:
            return text
        if _has_deepseek_reasoning_only(data):
            raise RuntimeError(
                "DeepSeek error: response only contained reasoning_content, not final message content. "
                "Increase --max-new-tokens or use a non-reasoning chat model so the model has enough budget to produce the final answer."
            )
        shape = _summarize_response_shape(data)
        raise RuntimeError(f"DeepSeek error: could not extract text from response; response shape: {shape}")

=======
                "Anthropic-compatible error: backend returned non-JSON content that could not be parsed"
            ) from exc
        if data.get("error"):
            raise RuntimeError(f"Anthropic-compatible error: {data['error']}")
        text = _extract_anthropic_text(data)
        if text:
            return text
        raise RuntimeError("Anthropic-compatible error: could not extract text from response")
>>>>>>> origin/main
