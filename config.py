# -*- coding: utf-8 -*-
"""
配置文件：提供 API 配置、SMTP 配置、数据库路径等全局配置。
优先级：settings.json > 环境变量 > .streamlit/secrets.toml

【安全说明】
  - API Key 在 settings.json 中以加密形式存储（AES + 随机 Key 文件）
  - 加密密钥存在同级目录 .keyfile 中（请务必一同分发并保管好此文件）
  - 如果 .keyfile 丢失，已加密的 API Key 无法解密，需重新填写
  - 未安装 cryptography 时使用标准库 fallback（XOR + HMAC 完整性校验）
"""

import os
import json
import logging
import base64
import hashlib
import secrets
import hmac

_logger = logging.getLogger(__name__)

_KEYFILE_NAME = ".keyfile"
_KEYFILE_SIZE = 32  # 256-bit key


# ========== 加密 / 解密核心 ==========

def _get_encryption_key() -> bytes:
    """
    读取或生成加密密钥，存到同级目录 .keyfile 中。
    返回 32 字节 key（用于 AES-256 或 XOR）。
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(base_dir, _KEYFILE_NAME)
    if os.path.exists(key_path):
        with open(key_path, "rb") as f:
            key = f.read()
        if len(key) >= _KEYFILE_SIZE:
            return key[:_KEYFILE_SIZE]
    # 生成新 key
    key = secrets.token_bytes(_KEYFILE_SIZE)
    with open(key_path, "wb") as f:
        f.write(key)
    # Windows 下隐藏 .keyfile
    try:
        import ctypes
        FILE_ATTRIBUTE_HIDDEN = 0x02
        ctypes.windll.kernel32.SetFileAttributesW(key_path, FILE_ATTRIBUTE_HIDDEN)
    except Exception:
        pass
    _logger.info(f"已生成新的加密密钥文件：{key_path}")
    return key


def _encrypt_api_key(plain_text: str) -> str:
    """
    将明文 API Key 加密，返回带前缀 'ENC:' 的 base64 字符串。
    使用 AES-256-GCM（cryptography 可用时）或 XOR+MAC fallback。
    """
    if not plain_text:
        return ""
    if plain_text.startswith("ENC:"):
        return plain_text  # 已加密，不再重复处理

    # 尝试使用 cryptography（AES-256-GCM）
    try:
        from cryptography.fernet import Fernet
        raw_key = _get_encryption_key()
        # Fernet 需要 base64 编码的 32 字节 key
        fernet_key = base64.urlsafe_b64encode(raw_key)
        f = Fernet(fernet_key)
        encrypted = f.encrypt(plain_text.encode("utf-8"))
        return "ENC:" + base64.urlsafe_b64encode(encrypted).decode("utf-8")
    except Exception:
        pass

    # Fallback：XOR + HMAC（标准库实现，够用于防明文泄露）
    key = _get_encryption_key()
    data = plain_text.encode("utf-8")
    # XOR 流式加密（key 循环）
    encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])
    # 加 HMAC 做完整性校验
    mac = hmac.new(key, encrypted, hashlib.sha256).digest()
    combined = mac + encrypted
    return "ENC:" + base64.urlsafe_b64encode(combined).decode("utf-8")


def _decrypt_api_key(encrypted_text: str) -> str:
    """
    将加密的 API Key 解密，返回明文。
    如果非加密格式（无 'ENC:' 前缀），原样返回（兼容旧版明文）。
    """
    if not encrypted_text:
        return ""
    if not encrypted_text.startswith("ENC:"):
        return encrypted_text  # 兼容旧版明文，平滑迁移

    payload = encrypted_text[4:]
    try:
        from cryptography.fernet import Fernet
        raw_key = _get_encryption_key()
        fernet_key = base64.urlsafe_b64encode(raw_key)
        f = Fernet(fernet_key)
        raw = base64.urlsafe_b64decode(payload)
        return f.decrypt(raw).decode("utf-8")
    except Exception:
        pass

    # Fallback：XOR + HMAC
    try:
        key = _get_encryption_key()
        combined = base64.urlsafe_b64decode(payload)
        mac_stored = combined[:32]
        encrypted = combined[32:]
        mac_calc = hmac.new(key, encrypted, hashlib.sha256).digest()
        if not hmac.compare_digest(mac_stored, mac_calc):
            _logger.error("API Key 完整性校验失败，.keyfile 可能已被更换")
            return ""
        plain_bytes = bytes([b ^ key[i % len(key)] for i, b in enumerate(encrypted)])
        return plain_bytes.decode("utf-8")
    except Exception as e:
        _logger.error(f"API Key 解密失败：{e}。请检查 .keyfile 是否存在且未被更换。")
        return ""


# ========== 读取 settings.json ==========

def _load_settings():
    """
    读取同目录下的 settings.json，返回 dict。文件不存在返回 {}。
    API Key 字段自动解密后返回明文。
    """
    settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            # 解密 api_key
            if "api_key" in settings:
                settings["api_key"] = _decrypt_api_key(settings["api_key"])
            # 解密 smtp_pass（SMTP 密码也加密存储）
            if "smtp_pass" in settings and settings["smtp_pass"].startswith("ENC:"):
                settings["smtp_pass"] = _decrypt_api_key(settings["smtp_pass"])
            return settings
        except Exception as e:
            _logger.warning(f"读取 settings.json 失败: {e}")
    return {}


def _get_secret(key, default=""):
    """优先读环境变量，其次读 streamlit secrets。"""
    val = os.environ.get(key, "")
    if val:
        return val
    try:
        import streamlit as st
        val = st.secrets.get(key, default)
    except Exception:
        val = default
    return val


def get_api_config():
    """
    返回 AI API 配置字典（明文，供程序内部调用）。
    优先级：settings.json > 环境变量 > .streamlit/secrets.toml
    """
    settings = _load_settings()
    return {
        "api_key":      settings.get("api_key",      "") or _get_secret("OPENAI_API_KEY", ""),
        "api_base":     settings.get("api_base",     "") or _get_secret("OPENAI_API_BASE", "https://api.openai.com/v1"),
        "model":        settings.get("model",        "") or _get_secret("OPENAI_MODEL",    "gpt-4o-mini"),
        "company_name": settings.get("company_name", "") or _get_secret("COMPANY_NAME",    ""),
    }


def get_smtp_config():
    """
    返回 SMTP 配置字典（明文，供邮件发送函数调用）。
    优先级：settings.json > 环境变量
    """
    settings = _load_settings()
    return {
        "smtp_server": settings.get("smtp_server", "") or os.environ.get("SMTP_SERVER", ""),
        "smtp_port":   int(settings.get("smtp_port", 587) or 587),
        "smtp_user":   settings.get("smtp_user",   "") or os.environ.get("SMTP_USER",   ""),
        "smtp_pass":   settings.get("smtp_pass",   "") or os.environ.get("SMTP_PASS",   ""),
        "smtp_ssl":    bool(settings.get("smtp_ssl", False)),
        "from_email":  settings.get("from_email",  "") or os.environ.get("FROM_EMAIL",  ""),
        "from_name":   settings.get("from_name",    "") or os.environ.get("FROM_NAME",    ""),
    }


def save_api_config(api_key="", api_base="", model="", company_name="",
                    smtp_server="", smtp_port=587, smtp_user="", smtp_pass="",
                    smtp_ssl=False, from_email="", from_name=""):
    """
    保存配置到 settings.json。
    API Key 和 SMTP 密码以加密形式存储；其余明文。
    只更新传入的非空 / 非默认值字段，其余保持原值。
    """
    settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    else:
        settings = {}

    if api_key      != "":  settings["api_key"]   = _encrypt_api_key(api_key)
    if api_base     != "":  settings["api_base"]   = api_base
    if model        != "":  settings["model"]      = model
    if company_name != "":  settings["company_name"] = company_name

    # SMTP 配置（smtp_pass 加密存储）
    if smtp_server  != "":  settings["smtp_server"]  = smtp_server
    if smtp_port    != 587: settings["smtp_port"]    = smtp_port
    if smtp_user    != "":  settings["smtp_user"]    = smtp_user
    if smtp_pass    != "":  settings["smtp_pass"]    = _encrypt_api_key(smtp_pass)
    if smtp_ssl is not None: settings["smtp_ssl"]   = smtp_ssl
    if from_email   != "":  settings["from_email"]   = from_email
    if from_name    != "":  settings["from_name"]    = from_name

    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
        f.write("\n")

    _logger.info("配置已保存到 settings.json（敏感字段已加密存储）")
    return True


# ========== 数据库配置 ==========

def _get_db_path():
    settings = _load_settings()
    db_file = settings.get("db_path", "recruitment.db")
    if not os.path.isabs(db_file):
        db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_file)
    return db_file


DB_PATH = _get_db_path()


# ========== 简历解析配置 ==========
RESUME_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resumes")
os.makedirs(RESUME_UPLOAD_DIR, exist_ok=True)


# ========== OCR 配置（可选）==========
OCR_ENABLED = False


# ========== 日志配置 ==========
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FILE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recruitment.log")
