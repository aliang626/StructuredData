# coding: utf-8
import json
import aiohttp
import ssl
import asyncio
import threading
import time

# 大模型API配置
APP_ID = "20250626AN152419J2Rk"
APP_SECRET = "1292677B543A4638B4CD1757AD5494FA"
BASE_URL = "https://hecc.ai.cnooc:30016/openapi/5tgnowdx"

class LLMClient:
    """改进版大模型客户端，解决事件循环问题"""
    
    def __init__(self):
        self.app_id = APP_ID
        self.app_secret = APP_SECRET
        self.base_url = BASE_URL
        self._loop_lock = threading.Lock()
        self._current_loop = None
        self._session = None
        self._ssl_context = None

    def create_headers(self):
        """创建请求头"""
        return {
            "authorization": f"Bearer {self.app_id}:{self.app_secret}",
            "Content-Type": "application/json; charset=UTF-8"
        }

    def gen_params(self, content):
        """生成请求参数"""
        return {
            "max_tokens": 8192,
            "messages": [
                {
                    "role": "user",
                    "content": content,
                    "name": "string"
                }
            ],
            "stream": True,
            "temperature": 0.01,  # 降低温度，提高输出稳定性
            "top_p": 0.01,        # 降低top_p，减少随机性
            "frequency_penalty": 0,  # 减少频率惩罚
            "presence_penalty": 0    # 减少存在惩罚
        }

    def _get_ssl_context(self):
        """获取SSL上下文"""
        if self._ssl_context is None:
            self._ssl_context = ssl.create_default_context()
            self._ssl_context.check_hostname = False
            self._ssl_context.verify_mode = ssl.CERT_NONE
        return self._ssl_context

    async def generate(self, content):
        """异步生成内容 - 改进版本"""
        headers = self.create_headers()
        data = json.dumps(self.gen_params(content=content))
        ssl_context = self._get_ssl_context()

        full_response = ""
        session = None
        
        try:
            # 创建新的session，避免复用问题
            session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=120, connect=30),  # 总超时2分钟，连接超时30秒
                connector=aiohttp.TCPConnector(ssl=ssl_context, limit=10)
            )
            
            async with session.post(
                self.base_url,
                data=data,
                headers=headers,
                ssl=ssl_context
            ) as response:
                if response.status != 200:
                    print(f"API调用失败，状态码: {response.status}")
                    return ""
                
                async for line in response.content:
                    if line:
                        try:
                            decoded_line = line.decode("utf-8").strip()
                            if decoded_line and "[DONE]" not in decoded_line:
                                decoded_line = decoded_line.replace("data:", "")
                                try:
                                    json_data = json.loads(decoded_line)
                                    delta_content = json_data["choices"][0]["delta"].get("content", "")
                                    if delta_content:
                                        full_response += delta_content
                                except (json.JSONDecodeError, KeyError, IndexError) as e:
                                    print(f"解析响应行时出错: {e}")
                                    continue
                        except Exception as e:
                            print(f"处理响应行时出错: {e}")
                            continue
                            
        except asyncio.TimeoutError:
            print("大模型API调用超时")
            return ""
        except Exception as e:
            print(f"大模型API调用失败: {str(e)}")
            return ""
        finally:
            # 确保session被正确关闭
            if session:
                try:
                    await session.close()
                except Exception as e:
                    print(f"关闭session时出错: {e}")
            
        return full_response.strip()

    def generate_sync(self, content):
        """同步生成内容（供非异步环境调用）- 完全重写版本"""
        try:
            # 使用asyncio.run，它会自动管理事件循环
            return asyncio.run(self.generate(content))
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                print("检测到事件循环已关闭，尝试重新创建...")
                # 如果事件循环已关闭，尝试重新创建
                try:
                    # 清理可能存在的旧循环
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.stop()
                        if not loop.is_closed():
                            loop.close()
                    except:
                        pass
                    
                    # 创建新的事件循环
                    if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        return loop.run_until_complete(self.generate(content))
                    finally:
                        try:
                            # 清理事件循环
                            pending = asyncio.all_tasks(loop)
                            if pending:
                                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                            loop.close()
                        except Exception as cleanup_error:
                            print(f"清理事件循环时出错: {cleanup_error}")
                except Exception as retry_error:
                    print(f"重新创建事件循环失败: {retry_error}")
                    return ""
            else:
                print(f"运行时错误: {e}")
                return ""
        except Exception as e:
            print(f"同步生成内容失败: {str(e)}")
            return ""

    def generate_sync_simple(self, content):
        """简化版同步生成内容，避免复杂的事件循环管理"""
        try:
            # 使用asyncio.run，它会自动管理事件循环
            return asyncio.run(self.generate(content))
        except Exception as e:
            print(f"简化版同步生成内容失败: {str(e)}")
            # 如果asyncio.run失败，回退到传统方法
            try:
                # 清理可能存在的旧循环
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.stop()
                    if not loop.is_closed():
                        loop.close()
                except:
                    pass
                
                # 创建新的事件循环
                if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    result = loop.run_until_complete(self.generate(content))
                    return result
                finally:
                    try:
                        # 清理事件循环
                        pending = asyncio.all_tasks(loop)
                        if pending:
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        loop.close()
                    except Exception as cleanup_error:
                        print(f"清理事件循环时出错: {cleanup_error}")
            except Exception as fallback_error:
                print(f"回退方法也失败: {str(fallback_error)}")
                return ""

    def __del__(self):
        """析构函数，确保资源被正确清理"""
        try:
            if self._session:
                # 这里不能直接await，因为析构函数不能是async
                pass
        except:
            pass
