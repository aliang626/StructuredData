import requests
import time
import json
import urllib.parse
from datetime import datetime, timedelta


class SSOService:
    """中海油单点登录服务类"""
    
    def __init__(self):
        # 中海油SSO配置
        self.base_url = "http://10.77.78.162/apigateway"
        self.app_name = "DApi"
        self.app_id = "880CADF172AC4ABD8864440804EE216F"
        self.api_token = "BVXUPHSWDEHIIQMU"
        
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
            
            # 构造token验证请求
            url = f"{self.base_url}/zhySdk/tokenCheck"
            
            # 构造query参数并进行URL编码
            query_data = {
                "jsonObj": {
                    "token": token
                }
            }
            
            # URL编码query参数
            query_json = json.dumps(query_data, ensure_ascii=False)
            query_encoded = urllib.parse.quote(query_json)
            
            params = {
                "appCode": app_code,
                "query": query_encoded
            }
            
            # 请求头
            headers = {
                "apiToken": self.api_token,
                "Content-Type": "application/json"
            }
            
            print(f"验证token请求: {url}")
            print(f"请求参数: {params}")
            print(f"请求头: {headers}")
            
            # 发送验证请求
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}...")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # 检查返回的状态码
                    if result.get('code') == 200:
                        # 验证成功，提取用户信息
                        user_data = result.get('data', {})
                        user_info = self._extract_user_info(user_data, token)
                        
                        return {
                            "success": True,
                            "user": user_info,
                            "message": "Token验证成功"
                        }
                    else:
                        error_msg = result.get('msg', '未知错误')
                        print(f"Token验证失败: {error_msg}")
                        return {
                            "success": False,
                            "error": f"Token验证失败: {error_msg}"
                        }
                        
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {e}")
                    print(f"原始响应: {response.text}")
                    return {
                        "success": False,
                        "error": "Token验证接口返回格式异常"
                    }
            else:
                print(f"HTTP请求失败: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Token验证请求失败: HTTP {response.status_code}"
                }
                
        except Exception as e:
            print(f"Token验证异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Token验证异常: {str(e)}"
            }
    
    def _extract_user_info(self, user_data, token):
        """从验证结果中提取用户信息"""
        if not user_data:
            # 如果没有用户数据，生成默认信息
            user_id = hash(token) % 10000
            return {
                "id": f"sso_{user_id}",
                "username": f"sso_user_{user_id % 1000}",
                "name": "SSO用户",
                "role": "user",
                "avatar": "",
                "email": "",
                "department": "中海油",
                "phone": "",
                "token": token,
                "loginType": "sso"
            }
        
        # 根据实际返回的用户信息结构提取数据
        user_info = {
            "id": user_data.get("userid", f"sso_{hash(token) % 10000}"),
            "username": user_data.get("username", "unknown"),
            "name": user_data.get("ryxm", user_data.get("name", "SSO用户")),
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
        
        print(f"提取的用户信息: {user_info}")
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
