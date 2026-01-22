import requests
import time
import json
import urllib.parse
from datetime import datetime, timedelta


class SSOService:
    """中海油单点登录服务类"""
    
    def __init__(self):
        # 中海油SSO配置（生产环境）
        self.base_url = "http://10.77.78.223/apigateway"
        self.app_name = "DApi"
        self.app_id = "880CADF172AC4ABD8864440804EE216F"
        self.api_token = "OCXQURVUFYIRCIHQ"
        
        # appCode缓存（有效期2小时）
        self._app_code = None
        self._app_code_expire_time = None
    
    def get_timestamp(self):
        """获取当前毫秒时间戳的前8位"""
        timestamp = str(int(time.time() * 1000))
        return timestamp[:8]
    
    def get_app_code(self):
        """获取appCode，带缓存机制"""
        try:
            # 检查缓存是否有效
            if (self._app_code and self._app_code_expire_time and 
                datetime.now() < self._app_code_expire_time):
                print(f"使用缓存的appCode: {self._app_code}")
                return self._app_code
            
            # 获取新的appCode
            timestamp = self.get_timestamp()
            url = f"{self.base_url}/appauth/getappid"
            
            params = {
                "appName": self.app_name,
                "appId": self.app_id,
                "timeStamp": timestamp
            }
            
            print(f"请求appCode: {url}")
            print(f"请求参数: {params}")
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                # 根据实际返回格式解析appCode
                app_code = response.text.strip()
                
                # 如果返回的是JSON格式，需要解析
                try:
                    result = response.json()
                    if result.get('code') == 200:
                        app_code = result.get('data', app_code)
                except:
                    # 如果不是JSON，直接使用text内容
                    pass
                
                # 缓存appCode（有效期2小时）
                self._app_code = app_code
                self._app_code_expire_time = datetime.now() + timedelta(hours=2)
                
                print(f"获取到新appCode: {app_code}")
                return app_code
            else:
                print(f"获取appCode失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"获取appCode异常: {str(e)}")
            return None
    
    def verify_token(self, token):
        """验证token并获取用户信息"""
        try:
            if not token:
                return {"success": False, "error": "Token不能为空"}
            
            # 获取appCode
            app_code = self.get_app_code()
            if not app_code:
                return {"success": False, "error": "获取appCode失败"}
            
            # 构造token验证请求（生产环境）
            url = f"{self.base_url}/zhy/tokenCheck"
            
            # 构造query参数并进行URL编码
            query_data = {
                "jsonObj": {
                    "token": token
                }
            }
            
            # URL编码query参数 - 使用紧凑格式（无空格）与甲方Postman一致
            query_json = json.dumps(query_data, ensure_ascii=False, separators=(',', ':'))
            query_encoded = urllib.parse.quote(query_json)
            
            params = {
                "appCode": app_code,
                "query": query_encoded
            }
            

            headers = {
                "apiToken": self.api_token
            }
            

            print("开始SSO Token验证请求")
            print(f"   - 验证URL: {url}")
            print(f"   - Token长度: {len(token)}")
            print(f"   - Token: {token}")
            print(f"   - AppCode: {app_code}")
            print()
            print(f"Query参数构造过程:")
            print(f"   - 原始query_data: {query_data}")
            print(f"   - JSON序列化结果: {query_json}")
            print(f"   - URL编码长度: {len(query_encoded)}")
            print(f"   - URL编码结果: {query_encoded}")
            print()
            print(f"完整请求信息:")
            print(f"   - 请求方法: GET")
            print(f"   - 请求头: {headers}")
            print(f"   - 请求参数: {params}")
            print(f"   - 完整URL: {url}?appCode={app_code}&query={query_encoded}")
            print()
            
            # 构造完整URL（避免requests再次编码params）
            full_url = f"{url}?appCode={app_code}&query={query_encoded}"
            
            # 发送验证请求 - 使用完整URL避免双重编码
            response = requests.get(full_url, headers=headers, timeout=10)
            
            print("收到响应:")
            print(f"   - 响应状态码: {response.status_code}")
            print(f"   - 响应内容长度: {len(response.text)}")
            print(f"   - 响应Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"   - 响应头信息: {dict(response.headers)}")
            print(f"   - 实际请求URL: {response.url}")
            print()
            
            if response.status_code == 200:
                # 检查响应内容是否为空
                if not response.text or response.text.strip() == "":
                    print("SSO服务返回200状态码但响应内容为空")
                    return {
                        "success": False,
                        "error": "SSO服务返回空响应，Token可能无效或已过期"
                    }
                
                # 检查响应内容类型
                content_type = response.headers.get('Content-Type', '').lower()
                response_preview = response.text[:100] if response.text else ""
                
                print("响应内容分析:")
                print(f"   - 响应预览(前100字符): {response_preview}")
                print(f"   - 是否HTML格式: {response.text.strip().startswith('<')}")
                print(f"   - 是否JSON格式: {response.text.strip().startswith('{')}")
                print(f"   - Content-Type: {content_type}")
                
                if 'html' in content_type or response.text.strip().startswith('<'):
                    print("检测到HTML响应而非JSON!")
                    print("   可能原因: URL错误、服务异常或网络拦截")
                    print("=" * 80)
                    return {
                        "success": False,
                        "error": "SSO服务返回HTML页面，可能是错误页面或配置问题"
                    }
                
                print("开始JSON解析...")
                try:
                    result = response.json()
                    print("JSON解析成功!")
                    print(f"   - 响应数据结构: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                    if isinstance(result, dict):
                        print(f"   - code字段: {result.get('code', '无')}")
                        print(f"   - msg字段: {result.get('msg', '无')}")
                        print(f"   - data字段存在: {'是' if result.get('data') else '否'}")
                    print()
                    
                    # 简化校验：只要有响应数据就认为成功
                    if result and result.get('data'):
                        user_data = result.get('data', {})
                        
                        # 直接提取用户信息，不进行详细校验
                        user_info = self._extract_user_info_simple(user_data, token)
                        
                        print("SSO验证成功!")
                        print(f"   - 用户名: {user_info.get('username', 'unknown')}")
                        print(f"   - 姓名: {user_info.get('name', 'unknown')}")
                        print(f"   - 部门: {user_info.get('department', 'unknown')}")
                        print("=" * 80)
                        return {
                            "success": True,
                            "user": user_info,
                            "message": "Token验证成功"
                        }
                    else:
                        error_msg = result.get('msg', '未知错误')
                        print("SSO验证失败!")
                        print(f"   - 错误信息: {error_msg}")
                        print(f"   - 响应code: {result.get('code', '无')}")
                        print(f"   - 可能原因: Token无效、已过期或权限不足")
                        print("=" * 80)
                        return {
                            "success": False,
                            "error": f"Token验证失败: {error_msg}"
                        }
                        
                except json.JSONDecodeError as e:
                    print("JSON解析失败!")
                    print(f"   - 解析错误: {str(e)}")
                    print(f"   - 响应长度: {len(response.text)}")
                    print(f"   - 响应预览: {response.text[:100] if response.text else 'None'}")
                    print("   - 分析: 响应不是有效的JSON格式")
                    print("=" * 80)
                    
                    # 检查响应是否为空
                    if not response.text or response.text.strip() == "":
                        return {
                            "success": False,
                            "error": "SSO服务返回空响应"
                        }
                    
                    # 检查响应是否是HTML错误页面
                    if response.text.strip().startswith('<'):
                        return {
                            "success": False,
                            "error": "SSO服务返回HTML错误页面，可能服务不可用"
                        }
                    
                    # 检查是否是纯文本错误消息
                    if len(response.text.strip()) < 200 and not response.text.strip().startswith('{'):
                        print(f"收到纯文本响应: {response.text.strip()}")
                        return {
                            "success": False,
                            "error": f"SSO服务返回错误信息: {response.text.strip()[:100]}"
                        }
                    
                    return {
                        "success": False,
                        "error": "Token验证接口返回格式异常"
                    }
            else:
                print("HTTP请求失败!")
                print(f"   - 状态码: {response.status_code}")
                print(f"   - 状态文本: {response.reason}")
                print(f"   - 响应长度: {len(response.text)}")
                print(f"   - 响应预览: {response.text[:100] if response.text else 'None'}")
                print("   - 可能原因: 网络问题、服务不可用或认证失败")
                print("=" * 80)
                return {
                    "success": False,
                    "error": f"Token验证请求失败: HTTP {response.status_code}"
                }
                
        except Exception as e:
            print("Token验证发生异常!")
            print(f"   - 异常类型: {type(e).__name__}")
            print(f"   - 异常信息: {str(e)}")
            print("   - 这通常表示网络连接问题或系统错误")
            print("=" * 80)
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Token验证异常: {str(e)}"
            }
    
    def _validate_user_info(self, user_data):
        """校验用户信息是否有效"""
        if not user_data:
            return {
                "valid": False,
                "reason": "未返回用户信息"
            }
        
        # 检查必需的用户字段
        required_fields = {
            "userid": "用户ID",
            "username": "用户名", 
            "ryxm": "姓名"
        }
        
        missing_fields = []
        for field, field_name in required_fields.items():
            if not user_data.get(field):
                missing_fields.append(field_name)
        
        if missing_fields:
            return {
                "valid": False,
                "reason": f"缺少必需字段: {', '.join(missing_fields)}"
            }
        
        # 检查用户ID是否有效（不能为空或无效值）
        userid = user_data.get("userid", "").strip()
        if not userid or userid in ["", "null", "undefined", "0"]:
            return {
                "valid": False,
                "reason": "用户ID无效"
            }
        
        # 检查用户名是否有效
        username = user_data.get("username", "").strip()
        if not username or username in ["", "null", "undefined"]:
            return {
                "valid": False,
                "reason": "用户名无效"
            }
        
        # 检查姓名是否有效
        name = user_data.get("ryxm", "").strip()
        if not name or name in ["", "null", "undefined"]:
            return {
                "valid": False,
                "reason": "用户姓名无效"
            }
        
        # 可选：检查用户状态（如果有相关字段）
        user_status = user_data.get("status", "").strip()
        if user_status and user_status.lower() in ["disabled", "inactive", "locked", "suspended"]:
            return {
                "valid": False,
                "reason": f"用户状态异常: {user_status}"
            }
        
        # 检查部门信息（可选，但建议有）
        dept_name = user_data.get("bmmc", "").strip()
        if not dept_name:
            print("警告: 用户缺少部门信息")
        
        print(f"用户信息校验通过")
        return {
            "valid": True,
            "reason": "用户信息有效"
        }
    
    def _extract_user_info_simple(self, user_data, token):
        """简化的用户信息提取（保护隐私）"""
        # 简化提取，不进行严格校验
        user_info = {
            "id": user_data.get("userid", "unknown"),
            "username": user_data.get("username", "user"),
            "name": user_data.get("ryxm", "用户"),
            "role": "user",  # 默认角色
            "avatar": "",
            "email": "",
            "department": user_data.get("bmmc", ""),
            "phone": user_data.get("lxdh", ""),
            "token": token,
            "loginType": "sso"
            # 注意：不保存原始数据以保护隐私
        }
        
        return user_info

    def _extract_user_info(self, user_data, token):
        """从验证结果中提取用户信息"""
        # 注意：此方法调用前已经通过了用户信息校验
        # 所以这里不需要再生成默认信息
        
        # 根据已验证的用户信息结构提取数据
        user_info = {
            "id": user_data.get("userid"),
            "username": user_data.get("username"),
            "name": user_data.get("ryxm"),
            "role": self._determine_user_role(user_data),
            "avatar": "",
            "email": "",
            "department": user_data.get("bmmc", ""),
            "phone": user_data.get("lxdh", ""),
            "token": token,
            "loginType": "sso",
            # 保存原始数据以备后用
            "originalData": user_data
        }
        
        return user_info
    
    def _determine_user_role(self, user_data):
        """根据用户数据确定角色"""
        # 可以根据部门代码、职位等信息判断用户角色
        dept_code = user_data.get("bmdm", "")
        dept_name = user_data.get("bmmc", "")
        
        # 示例：如果是某些特定部门，设置为管理员
        admin_depts = ["系统管理", "IT部门", "信息中心"]
        if any(dept in dept_name for dept in admin_depts):
            return "admin"
        
        # 默认为普通用户
        return "user"
    
    def refresh_app_code(self):
        """强制刷新appCode"""
        self._app_code = None
        self._app_code_expire_time = None
        return self.get_app_code()


# 创建全局实例
sso_service = SSOService()
