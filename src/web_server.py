import json
import os
import secrets
from typing import Optional
import requests
from robyn import Robyn, Request, Response
from robyn.templating import JinjaTemplate
from aivoice_python import AIVoiceTTsControl
from .models.voice_settings import VoiceSettings

class TTSWebServer:
    def __init__(self, tts_control: AIVoiceTTsControl):
        self.app = Robyn(__file__)
        self.tts_control = tts_control
        self.sessions = {}
        self.template = JinjaTemplate("templates")
        
        # Discord OAuth2 settings - 環境変数から取得
        self.client_id = os.getenv("DISCORD_CLIENT_ID")
        self.client_secret = os.getenv("DISCORD_CLIENT_SECRET")
        self.redirect_uri = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8080/callback")
        
        self.setup_routes()
    
    async def get_user_voice_settings(self, user_id: str):
        """ユーザーの音声設定を取得（DB から）"""
        try:
            return await VoiceSettings.get_user_settings(user_id)
        except Exception as e:
            print(f"音声設定取得エラー: {e}")
            return {}
    
    async def save_user_voice_settings(self, user_id: str, settings: dict):
        """ユーザーの音声設定を保存（DB へ）"""
        try:
            await VoiceSettings.update_user_settings(user_id, settings)
        except Exception as e:
            print(f"音声設定保存エラー: {e}")
    
    def get_user_from_session(self, request: Request) -> Optional[dict]:
        # Robynのヘッダーアクセス方法に修正
        cookie_header = request.headers.get("cookie") or request.headers.get("Cookie") or ""
        if "session_id=" in cookie_header:
            session_id = cookie_header.split("session_id=")[1].split(";")[0]
            return self.sessions.get(session_id)
        return None
    
    def setup_routes(self):
        @self.app.get("/")
        def index(request: Request):
            user = self.get_user_from_session(request)
            return self.template.render_template("index.html", user=user)
        
        @self.app.get("/login")
        def login(request: Request):
            if not self.client_id:
                # 環境変数が設定されていない場合のデモモード
                demo_user = {
                    "id": "demo_user_123",
                    "username": "DemoUser",
                    "avatar_url": "https://cdn.discordapp.com/embed/avatars/0.png"
                }
                session_id = secrets.token_urlsafe(32)
                self.sessions[session_id] = demo_user
                
                return Response(
                    status_code=302,
                    headers={
                        "Location": "/",
                        "Set-Cookie": f"session_id={session_id}; Path=/; HttpOnly"
                    },
                    description="Redirecting to home"
                )
            
            discord_auth_url = (
                f"https://discord.com/api/oauth2/authorize"
                f"?client_id={self.client_id}"
                f"&redirect_uri={self.redirect_uri}"
                f"&response_type=code"
                f"&scope=identify"
            )
            
            return Response(
                status_code=302,
                headers={"Location": discord_auth_url},
                description="Redirecting to Discord"
            )
        
        @self.app.get("/callback")
        def callback(request: Request):
            code = request.query_params.get("code", None)
            if not code:
                return Response(status_code=400, headers={}, description="No authorization code")
            
            # Exchange code for access token
            token_data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri
            }
            
            token_response = requests.post(
                "https://discord.com/api/oauth2/token",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if token_response.status_code != 200:
                return Response(status_code=400, headers={}, description="Failed to get access token")
            
            access_token = token_response.json()["access_token"]
            
            # Get user info
            user_response = requests.get(
                "https://discord.com/api/users/@me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                return Response(status_code=400, headers={}, description="Failed to get user info")
            
            user_data = user_response.json()
            user_data["avatar_url"] = (
                f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png"
                if user_data.get("avatar") else
                "https://cdn.discordapp.com/embed/avatars/0.png"
            )
            
            # Create session
            session_id = secrets.token_urlsafe(32)
            self.sessions[session_id] = user_data
            
            return Response(
                status_code=302,
                headers={
                    "Location": "/",
                    "Set-Cookie": f"session_id={session_id}; Path=/; HttpOnly"
                },
                description="Login successful"
            )
        
        @self.app.get("/logout")
        def logout(request: Request):
            cookie_header = request.headers.get("cookie") or request.headers.get("Cookie") or ""
            if "session_id=" in cookie_header:
                session_id = cookie_header.split("session_id=")[1].split(";")[0]
                self.sessions.pop(session_id, None)
            
            return Response(
                status_code=302,
                headers={
                    "Location": "/",
                    "Set-Cookie": "session_id=; Path=/; HttpOnly; Max-Age=0"
                },
                description="Logged out"
            )
        
        @self.app.get("/api/voices")
        async def get_voices(request: Request):
            user = self.get_user_from_session(request)
            if not user:
                return Response(status_code=401, headers={}, description="Unauthorized")
            
            # データベースからユーザー設定を取得
            user_settings = await self.get_user_voice_settings(user["id"])
            
            return {
                "voices": self.tts_control.voice_names,
                "current_voice": user_settings.get("voice", self.tts_control.voice_names[0]),
                "settings": {
                    "pitch": user_settings.get("pitch", 1.0),
                    "speed": user_settings.get("speed", 1.0),
                    "volume": user_settings.get("volume", 1.0),
                    "pitchRange": user_settings.get("pitchRange", 1.0),
                    "middlePause": user_settings.get("middlePause", 150),
                    "longPause": user_settings.get("longPause", 300),
                    "styles": {
                        "J": user_settings.get("styleJ", 0.0),
                        "A": user_settings.get("styleA", 0.0),
                        "S": user_settings.get("styleS", 0.0)
                    }
                }
            }
        
        @self.app.post("/api/save-settings")
        async def save_settings(request: Request):
            user = self.get_user_from_session(request)
            if not user:
                return Response(status_code=401, headers={}, description="Unauthorized")
            
            try:
                data = json.loads(request.body)
                
                # データベースに設定を保存
                settings_data = {
                    "voice": data["voice"],
                    "pitch": data["settings"]["pitch"],
                    "speed": data["settings"]["speed"],
                    "volume": data["settings"]["volume"],
                    "pitchRange": data["settings"]["pitchRange"],
                    "middlePause": data["settings"]["middlePause"],
                    "longPause": data["settings"]["longPause"],
                    "styleJ": data["settings"]["styles"]["J"],
                    "styleA": data["settings"]["styles"]["A"],
                    "styleS": data["settings"]["styles"]["S"]
                }
                
                await self.save_user_voice_settings(user["id"], settings_data)
                return {"status": "success"}
                
            except Exception as e:
                print(f"設定保存エラー: {e}")
                return Response(status_code=500, headers={}, description=str(e))
    
    def start(self, host="localhost", port=8080):
        print(f"🌟 TTS Web Interface starting on http://{host}:{port}")
        if not self.client_id:
            print("📋 Demo mode: Discord OAuth2 not configured - using demo login")
        else:
            print("💫 Discord OAuth2 configured - real authentication enabled!")
        self.app.start(port=port)

# Global web server instance
web_server_instance = None

def create_web_server(tts_control: AIVoiceTTsControl):
    """Webサーバーインスタンスを作成（完全にDB基盤）"""
    global web_server_instance
    web_server_instance = TTSWebServer(tts_control)
    return web_server_instance
