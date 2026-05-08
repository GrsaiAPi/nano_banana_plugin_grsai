# -*- coding: utf-8 -*-
"""
Nano Banana 中转插件 - Grsai
通过 Grsai API 调用 nano-banana-fast 模型生成图片
"""

import os
import sys
import base64
import requests
import time
import json
from io import BytesIO
from PIL import Image
from datetime import datetime

# 导入 PySide6 组件用于创建自定义 UI
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QSpinBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from pathlib import Path

# 导入自定义控件
plugin_dir = Path(__file__).parent
generator_dir = plugin_dir.parent.parent.parent
sys.path.insert(0, str(generator_dir))
from gui.widget.no_wheel_combo_box import NoWheelComboBox
from gui import password_editor

# 导入插件通用工具
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from plugin_utils import load_plugin_config, update_plugin_param, get_plugin_params

# 保存插件文件路径，用于配置管理
_PLUGIN_FILE = __file__

# 默认参数
_default_params = {
    "api_key": "",
    "endpoint": "https://grsai.dakka.com.cn",
    "model": "nano-banana-fast",
    "request_timeout": 700,
    "download_timeout": 700,
    "retry_count": 3,
    # 新增下面两行
    "aspect_ratio": "auto",
    "image_size": "1K",
}

# 模型列表
AVAILABLE_MODELS = [
    # Nano Banana 系列
    "nano-banana-fast",
    "nano-banana",
    "nano-banana-pro",
    "nano-banana-pro-vt",
    "nano-banana-pro-cl",
    "nano-banana-pro-vip",
    "nano-banana-pro-4k-vip",
    "nano-banana-2",
    "nano-banana-2-cl",
    "nano-banana-2-4k-cl",
    # Gptimage2
    "gpt-image-2",
    "gpt-image-2-vip",
]

# 全局参数存储（由软件统一管理）
_global_params = _default_params.copy()
_global_params.update(load_plugin_config(_PLUGIN_FILE))

print(
    f"[Nano Banana Grsai] 插件初始化完成，API Key: {'已设置('+str(len(_global_params.get('api_key','')))+'字符)' if _global_params.get('api_key') else '未设置'}, Endpoint: {_global_params.get('endpoint', '')}"
)


def get_info():
    """返回插件信息"""
    return {
        "name": "Nano Banana 中转插件 - Grsai(官方)",
        "description": "通过Grsai API（https://grsai.ai）调用 nano-banana 系列及 gpt-image-2 等多种图像生成模型，支持分辨率和尺寸选择。注意：Grsai未与该平台达成合作，模型使用问题可通过Grsai官网联系在线客服解决。使用该平台时建议和Grsai控制台日志结合查看，平台如果未能成功下载图片可通过查看日志中的结果数据获取，图片有效期两小时。",
        "version": "2.0.2",
        "author": "GrsaiAPI",
    }


class PluginUI:
    """插件自定义 UI 类"""

    def __init__(self):
        # 不再维护独立的 params，直接使用全局参数
        self.widgets = {}

    def create_ui(self, parent_widget):
        """创建自定义 UI"""
        # 创建容器 widget
        container = QWidget(parent_widget)
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(153, 10, 10, 10)
        container.setLayout(layout)

        # API Key 输入
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("API Key:")
        api_key_label.setFixedWidth(100)
        api_key_label.setFont(QFont("Microsoft YaHei", 9))
        api_key_label.setStyleSheet("color: #CCCCCC;")

        self.widgets["api_key"] = password_editor.PasswordEditor(
            textChanged=lambda: self._update_param(
                "api_key", self.widgets["api_key"].text()
            ),
            default_text=_global_params["api_key"],
            placeholder="请输入 API Key",
        )
        self.widgets["api_key"].setFixedHeight(32)
        self.widgets["api_key"].editor.input.setFont(QFont("Microsoft YaHei", 9))

        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.widgets["api_key"])
        layout.addLayout(api_key_layout)

        # Endpoint 输入
        endpoint_layout = QHBoxLayout()
        endpoint_label = QLabel("Endpoint:")
        endpoint_label.setFixedWidth(100)
        endpoint_label.setFont(QFont("Microsoft YaHei", 9))
        endpoint_label.setStyleSheet("color: #CCCCCC;")

        self.widgets["endpoint"] = QLineEdit()
        self.widgets["endpoint"].setPlaceholderText("API 端点地址")
        self.widgets["endpoint"].setFont(QFont("Microsoft YaHei", 9))
        self.widgets["endpoint"].setFixedHeight(32)
        self.widgets["endpoint"].setStyleSheet(
            """
            QLineEdit {
                background-color: #2b2b2b;
                color: #CCCCCC;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #0d7377;
            }
        """
        )
        self.widgets["endpoint"].setText(_global_params["endpoint"])
        self.widgets["endpoint"].textChanged.connect(
            lambda text: self._update_param("endpoint", text)
        )

        endpoint_layout.addWidget(endpoint_label)
        endpoint_layout.addWidget(self.widgets["endpoint"])
        layout.addLayout(endpoint_layout)

        # 模型选择下拉框
        model_layout = QHBoxLayout()
        model_label = QLabel("模型:")
        model_label.setFixedWidth(100)
        model_label.setFont(QFont("Microsoft YaHei", 9))
        model_label.setStyleSheet("color: #CCCCCC;")

        self.widgets["model"] = NoWheelComboBox()
        self.widgets["model"].addItems(AVAILABLE_MODELS)
        self.widgets["model"].setCurrentText(
            _global_params.get("model", "nano-banana-fast")
        )
        self.widgets["model"].setFont(QFont("Microsoft YaHei", 9))
        self.widgets["model"].setFixedHeight(32)
        self.widgets["model"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.widgets["model"].currentTextChanged.connect(
            lambda text: self._update_param("model", text)
        )

        model_layout.addWidget(model_label)
        model_layout.addWidget(self.widgets["model"])
        layout.addLayout(model_layout)

        # ==================== 新增：图片比例 和 分辨率 ====================
        # 图片比例（根据模型动态更新选项）
        aspect_layout = QHBoxLayout()
        aspect_label = QLabel("图片比例:")
        aspect_label.setFixedWidth(100)
        aspect_label.setFont(QFont("Microsoft YaHei", 9))
        aspect_label.setStyleSheet("color: #CCCCCC;")

        self.widgets["aspect_ratio"] = NoWheelComboBox()
        self.widgets["aspect_ratio"].setFont(QFont("Microsoft YaHei", 9))
        self.widgets["aspect_ratio"].setFixedHeight(32)

        aspect_layout.addWidget(aspect_label)
        aspect_layout.addWidget(self.widgets["aspect_ratio"])
        layout.addLayout(aspect_layout)

        # 分辨率（仅 Nano Banana 系列）
        self.image_size_layout = QHBoxLayout()
        self.image_size_label = QLabel("分辨率:")
        self.image_size_label.setFixedWidth(100)
        self.image_size_label.setFont(QFont("Microsoft YaHei", 9))
        self.image_size_label.setStyleSheet("color: #CCCCCC;")

        self.widgets["image_size"] = NoWheelComboBox()
        self.widgets["image_size"].setFont(QFont("Microsoft YaHei", 9))
        self.widgets["image_size"].setFixedHeight(32)

        self.image_size_layout.addWidget(self.image_size_label)
        self.image_size_layout.addWidget(self.widgets["image_size"])
        layout.addLayout(self.image_size_layout)

        # ==================== 动态更新 + 绑定事件 ====================

        # ==================== 动态更新 + 绑定事件 ====================

        def update_options(model_text):
            if not model_text:
                return

            print(f"[DEBUG] update_options 被调用，当前模型: {model_text}")

            # 临时阻塞 aspect_ratio 的信号，防止循环触发
            try:
                self.widgets["aspect_ratio"].currentTextChanged.disconnect()
            except:
                pass

            # ==== 1. 处理图片比例 (aspect_ratio) ====
            self.widgets["aspect_ratio"].clear()

            # 判断模型类型
            is_gpt_image = model_text == "gpt-image-2"
            is_gpt_image_vip = model_text == "gpt-image-2-vip"
            is_nano_banana_2 = model_text in [
                "nano-banana-2",
                "nano-banana-2-cl",
                "nano-banana-2-4k-cl",
            ]

            if is_gpt_image:
                options = [
                    "auto",
                    "1024x1024",
                    "1536x1024",
                    "1024x1536",
                    "1448x1086",
                    "1086x1448",
                    "1774x887",
                    "887x1774",
                ]
                self.image_size_label.hide()
                self.widgets["image_size"].hide()
            elif is_gpt_image_vip:
                options = [
                    "auto",
                    "1024x1024",
                    "2048x2048",
                    "2880x2880",
                    "1536x1024",
                    "2048x1360",
                    "3504x2336",
                    "1024x1536",
                    "1360x2048",
                    "2336x3504",
                    "1448x1086",
                    "2048x1632",
                    "3200x2560",
                    "1086x1448",
                    "1632x2048",
                    "2560x3200",
                    "1774x887",
                    "2048x1152",
                    "3840x2160",
                    "887x1774",
                    "1152x2048",
                    "2160x3840",
                    "2048x880",
                    "3840x1648",
                    "880x2048",
                    "1648x3840",
                    "688x2048",
                    "1280x3840",
                    "2048x688",
                    "3840x1280",
                    "2048x1024",
                    "3840x1920",
                    "1024x2048",
                    "1920x3840",
                ]
                self.image_size_label.hide()
                self.widgets["image_size"].hide()
            elif is_nano_banana_2:
                # nano-banana-2 系列（额外支持 1:4, 4:1, 1:8, 8:1）
                options = [
                    "auto",
                    "1:1",
                    "16:9",
                    "9:16",
                    "4:3",
                    "3:4",
                    "3:2",
                    "2:3",
                    "5:4",
                    "4:5",
                    "21:9",
                    "1:4",
                    "4:1",
                    "1:8",
                    "8:1",
                ]
                self.image_size_label.show()
                self.widgets["image_size"].show()
            else:
                # 其他 nano-banana 系列（基础比例）
                options = [
                    "auto",
                    "1:1",
                    "16:9",
                    "9:16",
                    "4:3",
                    "3:4",
                    "3:2",
                    "2:3",
                    "5:4",
                    "4:5",
                    "21:9",
                ]
                # 新增：nano-banana 和 nano-banana-fast 不显示分辨率
                if model_text in ["nano-banana", "nano-banana-fast"]:
                    self.image_size_label.hide()
                    self.widgets["image_size"].hide()
                else:
                    self.image_size_label.show()
                    self.widgets["image_size"].show()

            self.widgets["aspect_ratio"].addItems(options)

            # === 关键修复：恢复保存的 aspect_ratio ===
            saved_ratio = str(_global_params.get("aspect_ratio", "auto")).strip()
            available = [
                self.widgets["aspect_ratio"].itemText(i)
                for i in range(self.widgets["aspect_ratio"].count())
            ]

            if saved_ratio in available and saved_ratio != "":
                self.widgets["aspect_ratio"].setCurrentText(saved_ratio)
                print(f"[DEBUG] aspect_ratio 成功恢复: {saved_ratio}")
            else:
                self.widgets["aspect_ratio"].setCurrentText("auto")
                print(
                    f"[DEBUG] aspect_ratio 使用默认 auto (保存值 '{saved_ratio}' 不匹配当前模型)"
                )

            # 重新绑定 aspect_ratio 变化事件
            self.widgets["aspect_ratio"].currentTextChanged.connect(
                lambda text: self._update_param("aspect_ratio", text)
            )

            # === 2. 处理分辨率 image_size ===
            self.widgets["image_size"].clear()
            model_lower = model_text.lower().strip()

            if model_lower in ["nano-banana-2-cl", "nano-banana-pro-vip"]:
                self.widgets["image_size"].addItems(["1K", "2K"])
                default_size = "1K"
            elif model_lower in ["nano-banana-2-4k-cl", "nano-banana-pro-4k-vip"]:
                self.widgets["image_size"].addItems(["4K"])
                default_size = "4K"
            elif "nano-banana" in model_lower:
                self.widgets["image_size"].addItems(["1K", "2K", "4K"])
                default_size = (
                    "2K" if ("pro" in model_lower or "2" in model_lower) else "1K"
                )
            elif "gpt-image-2-vip" in model_lower:
                self.widgets["image_size"].addItems(["1K", "2K", "4K"])
                default_size = "1K"
            elif "gpt-image-2" in model_lower:
                self.widgets["image_size"].addItems(["1K"])
                default_size = "1K"
            else:
                self.widgets["image_size"].addItems(["1K"])
                default_size = "1K"

            saved_size = str(_global_params.get("image_size", default_size)).strip()
            available_sizes = [
                self.widgets["image_size"].itemText(i)
                for i in range(self.widgets["image_size"].count())
            ]

            if saved_size in available_sizes and saved_size != "":
                self.widgets["image_size"].setCurrentText(saved_size)
            else:
                self.widgets["image_size"].setCurrentText(default_size)

            # 绑定 image_size 变化事件
            try:
                self.widgets["image_size"].currentTextChanged.disconnect()
            except:
                pass
            self.widgets["image_size"].currentTextChanged.connect(
                lambda text: self._update_param("image_size", text)
            )

        # ====================== 绑定与初始化 ======================
        # 先断开旧信号（防止重复绑定）
        try:
            self.widgets["model"].currentTextChanged.disconnect(update_options)
        except:
            pass

        self.widgets["model"].currentTextChanged.connect(update_options)

        # 初始化时执行（重要）
        update_options(self.widgets["model"].currentText())
        # ============================================================

        # 请求超时时间输入
        request_timeout_layout = QHBoxLayout()
        request_timeout_label = QLabel("请求超时(秒):")
        request_timeout_label.setFixedWidth(100)
        request_timeout_label.setFont(QFont("Microsoft YaHei", 9))
        request_timeout_label.setStyleSheet("color: #CCCCCC;")

        self.widgets["request_timeout"] = QSpinBox()
        self.widgets["request_timeout"].setMinimum(100)
        self.widgets["request_timeout"].setMaximum(999999)
        self.widgets["request_timeout"].setValue(
            _global_params.get("request_timeout", 700)
        )
        self.widgets["request_timeout"].setFont(QFont("Microsoft YaHei", 9))
        self.widgets["request_timeout"].setFixedHeight(32)
        self.widgets["request_timeout"].setStyleSheet(
            """
            QSpinBox {
                background-color: #2b2b2b;
                color: #CCCCCC;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px;
            }
            QSpinBox:focus {
                border: 1px solid #0d7377;
            }
        """
        )
        self.widgets["request_timeout"].valueChanged.connect(
            lambda value: self._update_param("request_timeout", value)
        )

        request_timeout_layout.addWidget(request_timeout_label)
        request_timeout_layout.addWidget(self.widgets["request_timeout"])
        layout.addLayout(request_timeout_layout)

        # 下载超时时间输入
        download_timeout_layout = QHBoxLayout()
        download_timeout_label = QLabel("下载超时(秒):")
        download_timeout_label.setFixedWidth(100)
        download_timeout_label.setFont(QFont("Microsoft YaHei", 9))
        download_timeout_label.setStyleSheet("color: #CCCCCC;")

        self.widgets["download_timeout"] = QSpinBox()
        self.widgets["download_timeout"].setMinimum(50)
        self.widgets["download_timeout"].setMaximum(999999)
        self.widgets["download_timeout"].setValue(
            _global_params.get("download_timeout", 700)
        )
        self.widgets["download_timeout"].setFont(QFont("Microsoft YaHei", 9))
        self.widgets["download_timeout"].setFixedHeight(32)
        self.widgets["download_timeout"].setStyleSheet(
            """
            QSpinBox {
                background-color: #2b2b2b;
                color: #CCCCCC;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px;
            }
            QSpinBox:focus {
                border: 1px solid #0d7377;
            }
        """
        )
        self.widgets["download_timeout"].valueChanged.connect(
            lambda value: self._update_param("download_timeout", value)
        )

        download_timeout_layout.addWidget(download_timeout_label)
        download_timeout_layout.addWidget(self.widgets["download_timeout"])
        layout.addLayout(download_timeout_layout)

        # 重试次数输入
        retry_layout = QHBoxLayout()
        retry_label = QLabel("重试次数:")
        retry_label.setFixedWidth(100)
        retry_label.setFont(QFont("Microsoft YaHei", 9))
        retry_label.setStyleSheet("color: #CCCCCC;")

        self.widgets["retry_count"] = QSpinBox()
        self.widgets["retry_count"].setMinimum(0)
        self.widgets["retry_count"].setMaximum(10)
        self.widgets["retry_count"].setValue(_global_params.get("retry_count", 3))
        self.widgets["retry_count"].setFont(QFont("Microsoft YaHei", 9))
        self.widgets["retry_count"].setFixedHeight(32)
        self.widgets["retry_count"].setStyleSheet(
            """
            QSpinBox {
                background-color: #2b2b2b;
                color: #CCCCCC;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 5px;
            }
            QSpinBox:focus {
                border: 1px solid #0d7377;
            }
        """
        )
        self.widgets["retry_count"].valueChanged.connect(
            lambda value: self._update_param("retry_count", value)
        )

        retry_layout.addWidget(retry_label)
        retry_layout.addWidget(self.widgets["retry_count"])
        layout.addLayout(retry_layout)

        # 说明文本

        info_label = QLabel(
            '<b>提示:通过<a href="https://grsai.ai">Grsai API</a> 调用 Gemini/Openai 系列模型(支持 nano-banana 图像生成模型)，支持参考图片，分辨率，尺寸</b><br>'
        )
        info_label.setFont(QFont("Microsoft YaHei", 10))
        info_label.setStyleSheet("color: #99999999;")
        info_label.setWordWrap(True)
        info_label.setOpenExternalLinks(True)  # 允许点击跳转链接
        layout.addWidget(info_label)

        return container

    def _update_param(self, key, value):
        """更新参数"""
        global _global_params
        # 更新全局参数
        _global_params[key] = value
        # 通过软件统一管理的工具函数保存
        update_plugin_param(_PLUGIN_FILE, key, value)

    def get_params(self):
        """返回当前参数"""
        return _global_params.copy()

    def load_params(self, params):
        """加载参数"""
        global _global_params
        _global_params.update(params)

        # 更新其他控件...
        if "model" in self.widgets and "model" in params:
            self.widgets["model"].setCurrentText(str(params["model"]))

        if _plugin_ui:
            # 强制刷新动态选项（解决切换/刷新后重置问题）
            if "model" in self.widgets:
                model_text = self.widgets["model"].currentText()
                # 使用 QTimer 延迟一点执行，避免信号冲突
                from PySide6.QtCore import QTimer

                QTimer.singleShot(
                    50,
                    lambda: self.widgets["model"].currentTextChanged.emit(model_text),
                )

        print(
            f"[DEBUG] load_params 执行完成，当前 aspect_ratio = {_global_params.get('aspect_ratio')}"
        )


# 全局 UI 实例
_plugin_ui = None


def create_ui(parent_widget):
    """创建自定义 UI（插件引擎调用）"""
    global _plugin_ui
    # 创建新的 UI 实例（直接使用全局参数）
    _plugin_ui = PluginUI()
    return _plugin_ui.create_ui(parent_widget)


def get_params():
    """获取当前参数（插件引擎调用）"""
    global _global_params
    # 直接返回全局参数（已从配置文件加载）
    print(
        f"[get_params] 返回参数: API Key={'已设置('+str(len(_global_params.get('api_key','')))+'字符)' if _global_params.get('api_key') else '未设置'}"
    )
    return _global_params.copy()


def load_params(params):
    """加载参数到UI（插件引擎调用，通常在打开插件页面时调用）"""
    global _global_params
    # 将全局参数同步到UI控件
    if _plugin_ui:
        _plugin_ui.load_params(_global_params)
        print(f"[load_params] 已将全局参数同步到UI")
    else:
        print(f"[load_params] UI尚未创建，跳过同步")


def send_grsai_draw_request(
    api_key,
    endpoint,
    model,
    prompt,
    reference_images,
    aspect_ratio="auto",
    image_size="1K",
    request_timeout=700,
    download_timeout=700,
):
    """
    Grsai 专用绘画接口（支持 nano-banana 系列 和 gpt-image-2）
    参考图片统一使用 Base64（两个模型都支持）
    """
    # 准备参考图片列表（Base64）
    urls = []
    for position, img_path in reference_images.items():
        if not os.path.exists(img_path) or os.path.getsize(img_path) == 0:
            continue
        try:
            with open(img_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            urls.append(image_data)  # 两个模型都传 Base64
            print(
                f"添加参考图片 (Base64): {position} -> {img_path} ({len(image_data)} chars)"
            )

        except Exception as e:
            print(f"加载参考图片失败 {img_path}: {e}")
            # 可以选择 continue 或 raise

    # 根据模型选择接口和 payload
    if model == "gpt-image-2" or model.startswith("gpt-image-2"):
        if ":" in aspect_ratio:
            aspect_ratio = "auto"

        api_path = "/v1/draw/completions"
        payload = {
            "model": model,
            "prompt": prompt,
            "urls": urls,
            "aspectRatio": aspect_ratio,  # 只传 aspectRatio
            "shutProgress": True,
            # 不要传 size、imageSize 等参数
        }
    else:
        if "x" in aspect_ratio:
            aspect_ratio = "auto"

        # Nano Banana 系列
        api_path = "/v1/draw/nano-banana"
        payload = {
            "model": model,
            "prompt": prompt,
            "urls": urls,
            "aspectRatio": aspect_ratio,
            "shutProgress": True,
        }

        # 只有支持分辨率的模型才传入 imageSize
        if model not in ["nano-banana", "nano-banana-fast"] and model != "gpt-image-2":
            payload["imageSize"] = image_size
            print(f"[DEBUG] 传入 imageSize: {image_size}")
        else:
            print(f"[DEBUG] 模型 {model} 不支持 imageSize 参数，已跳过")

    full_url = f"{endpoint.rstrip('/')}{api_path}"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    print(f"发送请求 → {full_url} | 模型: {model} | 参考图数量: {len(urls)}")

    # 发送请求
    response = requests.post(
        full_url, json=payload, headers=headers, timeout=request_timeout
    )

    if response.status_code != 200:
        error_text = response.text[:400]
        raise Exception(f"HTTP {response.status_code}: {error_text}")

    response_text = response.text.strip()

    # 如果整个响应就是 data: 开头，去掉前缀
    if response_text.startswith("data: "):
        response_text = response_text[6:].strip()
    else:
        response_text = response_text.strip()
        raise Exception(response_text)

    # 解析响应，提取图片 URL
    image_url = None

    try:
        data = json.loads(response_text)

        # 优先从 results 数组中取 url
        if (
            "results" in data
            and isinstance(data.get("results"), (list, tuple))
            and len(data["results"]) > 0
        ):
            result = data["results"][0]
            if isinstance(result, dict) and result.get("url"):
                image_url = result["url"]
                print(f"✓ 从 results 中获取图片 URL: {image_url}")

        # 兼容顶层 url 字段
        elif data.get("url"):
            image_url = data["url"]
            print(f"✓ 从顶层 url 字段获取图片 URL")

        # 处理失败情况
        if data.get("status") == "failed":
            raise Exception(json.dumps(data, ensure_ascii=False, indent=2))

    except json.JSONDecodeError:
        print(f"[WARN] 响应不是有效的 JSON 格式")

    # 如果没有获取到图片URL
    if not image_url:
        print(f"响应内容预览（前500字符）:\n{response.text[:500]}")
        raise Exception(
            "未能提取到图片URL，请前往 Grsai.ai 控制台日志中查看结果JSON，手动保存图片链接"
        )

    # 下载图片并转为 base64 返回
    try:
        print(f"正在下载生成图片: {image_url}")
        img_response = requests.get(image_url, timeout=download_timeout)
        if img_response.status_code != 200:
            raise Exception(f"下载失败 HTTP {img_response.status_code}")

        image_data_base64 = base64.b64encode(img_response.content).decode("utf-8")
        print("✓ 图片下载并转换为 base64 成功")
        return image_data_base64

    except Exception as e:
        raise Exception(f"下载生成的图片失败: {str(e)}")


def generate(context):
    """
    主生成函数 - 通过 Grsai API 调用 nano-banana-fast 模型生成图片

    参数:
        context: 字典，包含以下键:
            - prompt: 正向提示词
            - reference_images: 参考图片字典 {位置: 图片路径}
            - output_dir: 输出目录
            - plugin_params: 插件自定义参数 (api_key, endpoint)

    返回:
        生成的图片路径列表
    """
    print("\n" + "=" * 60)
    print("Nano Banana Grsai 插件开始生成")
    print("=" * 60)

    # 获取参数
    prompt = context.get("prompt", "")
    reference_images = context.get("reference_images", {})
    output_dir = context.get("output_dir", "")
    plugin_params = context.get("plugin_params", {})

    # 获取插件配置
    api_key = str(plugin_params.get("api_key", "")) if plugin_params else ""
    endpoint = (
        str(plugin_params.get("endpoint", "https://grsai.dakka.com.cn"))
        if plugin_params
        else "https://grsai.dakka.com.cn"
    )
    model = (
        str(plugin_params.get("model", "nano-banana-fast"))
        if plugin_params
        else "nano-banana-fast"
    )

    request_timeout = (
        int(plugin_params.get("request_timeout", 700)) if plugin_params else 700
    )
    download_timeout = (
        int(plugin_params.get("download_timeout", 700)) if plugin_params else 700
    )
    retry_count = int(plugin_params.get("retry_count", 3)) if plugin_params else 3

    # 新增：图片比例 和 分辨率
    # 新增：图片比例 和 分辨率
    aspect_ratio = (
        str(plugin_params.get("aspect_ratio", "auto")) if plugin_params else "auto"
    )
    image_size = str(plugin_params.get("image_size", "1K")) if plugin_params else "1K"

    print(f"\n===== 生成参数 =====")
    print(f"正向提示词: {prompt}")
    print(f"参考图片数量: {len(reference_images)}")
    print(
        f"API Key: {'已设置 (' + str(len(api_key)) + ' 字符)' if api_key else '未设置'}"
    )
    print(f"Endpoint: {endpoint}")
    print(f"模型: {model}")
    print(f"图片比例: {aspect_ratio}")

    # 修改：根据模型显示不同提示
    if model in ["nano-banana", "nano-banana-fast"]:
        print(f"分辨率: 不支持（已跳过）")
    elif model.startswith("gpt-image-2"):
        print(f"分辨率: 不支持（gpt-image-2 使用 aspectRatio）")
    else:
        print(f"分辨率: {image_size}")

    print(f"请求超时: {request_timeout}秒")
    print(f"下载超时: {download_timeout}秒")
    print(f"重试次数: {retry_count}")
    print(f"==================\n")

    # 验证 API Key
    if not api_key or api_key.strip() == "":
        error_msg = "❌ 错误: 未设置 API Key，请在插件设置中填写"
        print(error_msg)
        raise Exception(error_msg)

    # 验证 Endpoint
    if not endpoint or endpoint.strip() == "":
        error_msg = "❌ 错误: 未设置 Endpoint"
        print(error_msg)
        raise Exception(error_msg)

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    generated_files = []

    # 实现重试逻辑
    max_attempts = retry_count + 1  # 总尝试次数 = 初始尝试 + 重试次数
    for attempt in range(max_attempts):
        try:
            if attempt > 0:
                print(f"\n第 {attempt + 1}/{max_attempts} 次尝试...")
            else:
                print(f"正在调用 Grsai API...")

            # 发送 API 请求
            image_data_base64 = send_grsai_draw_request(
                api_key=api_key,
                endpoint=endpoint.strip().rstrip("/"),
                model=model,
                prompt=prompt,
                reference_images=reference_images,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
                request_timeout=700,
                download_timeout=700,
            )

            # 解码并保存图片
            image_data = base64.b64decode(image_data_base64)
            generated_image = Image.open(BytesIO(image_data))

            # 保存图片
            viewer_index = context.get("viewer_index", 0)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{viewer_index:04d}_gemini_{timestamp}.png"
            output_path = os.path.join(output_dir, filename)
            generated_image.save(output_path, "PNG")

            generated_files.append(output_path)
            print(f"✓ 成功生成图片: {output_path}")
            break  # 成功则跳出重试循环

        except Exception as e:
            is_last_attempt = attempt == max_attempts - 1
            error_str = str(e)

            try:
                error_data = json.loads(str(e))
                id = error_data.get("id")
                error_type = error_data.get("failure_reason")
                error_msg = error_data.get("error")
            except (json.JSONDecodeError, AttributeError):
                raise Exception(f"PLUGIN_ERROR:::{error_msg}")

            failure_type = f"任务ID: {id}\n"
            # # 根据Grsai平台的结果参数判断失败原因
            if error_type == "output_moderation":
                failure_type += "输出内容违规\n建议：降低提示词敏感度、避免暴力/色情/政治/儿童等内容"
                failure_type += f"\n违规内容：{error_msg}"
            elif error_type == "error":
                failure_type += f"任务失败，失败内容：{error_msg}\n可能是官方砍算力导致\n建议：晚点再重试（高峰期算力紧张）"
            else:
                failure_type = str(e)

            if is_last_attempt:
                error_content = (
                    f"生成失败（已尝试 {max_attempts} 次）\n\n原因：\n{failure_type}"
                )
                print(f"❌ {error_content}")
                import traceback

                traceback.print_exc()
                raise Exception(f"PLUGIN_ERROR:::{error_content}")

    print("\n" + "=" * 60)
    print(f"Nano Banana Grsai 插件完成，共生成 {len(generated_files)} 张图片")
    print("=" * 60 + "\n")

    return generated_files
