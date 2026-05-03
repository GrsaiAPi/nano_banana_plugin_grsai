# Nano Banana 中转插件-Grsai（官方）

> ⚠️ **重要说明：本插件为 GrsaiAPI 官方维护版本**

## 📌 背景

原 `Nano Banana 中转插件-Grsai` **并非 GrsaiAPI 官方提供**，而是由第三方开发者制作的非官方插件。由于原开发者已不再维护且无法取得联系，导致大量用户遇到以下问题：

- ❌ 模型无法使用
- ❌ Grsai 控制台显示“生成成功”，但字字动画不出图
- ❌ 仅支持 `nano-banana-fast`、`nano-banana-pro`、`nano-banana` 三个模型
- ❌ 使用 Gemini 流式格式，兼容性差
- ❌ 超时时间过短，任务未完成即报错

## ✅ 官方版本改进

本插件为 GrsaiAPI 官方接手维护的全新版本，更名为`Nano Banana 中转插件-Grsai（官方）`已全面优化：

### 1. 完善模型库

模型对照表：

1. **gemini-2.5-flash-image** 对应：
   - nano-banana：1-2k清晰度
   - nano-banana-fast：1-2k清晰度

2. **gemini-3-pro-image-preview** 对应：
   - nano-banana-pro（推荐）：1-4k清晰度高峰期稳定，偶有波动
   - nano-banana-pro-cl（推荐）：4k画质清晰，pro备用渠道，稳定速度快
   - nano-banana-pro-vt：高峰期不稳定，4k画质清晰
   - nano-banana-pro-vip：1-2k清晰度，付费渠道，稳定但贵
   - nano-banana-pro-4k-vip：4k清晰度，付费渠道，稳定但贵

3. **gemini-3.1-flash-image-preview** 对应：
   - nano-banana-2：1-4k清晰度
   - nano-banana-2-cl：1-2k清晰度
   - nano-banana-2-4k-cl：4k清晰度

4. **Chatgpt image 2.0** 对应：
   - gpt-image-2：仅支持1k清晰度
   - gpt-image-2-vip：支持1k/2k/4k清晰度，支持选择质量

渠道不同所以才有那么多版本，按需选择！

💡 渠道不同导致模型版本较多，请按需选择。
⚠️ 具体信息看GrsaiAPi模型列表：https://grsai.ai/dashboard/models

### 2. 更多参数选项
- ✅ 支持选择图片尺寸和分辨率
- ✅ 超时时间延长至 **500 秒**，不再因任务未完成而报错

### 3. 接口重构
- 修改请求接口，提升稳定性
- 优化用户反馈最多的问题

## 📥 安装方法

1. **关闭字字动画软件**

2. **找到插件安装目录**
以我的参考：D:\软件\字字动画_internal\plugins\image_plugins
   
3. **删除旧版插件文件夹**
删除该目录下的 nano_banana_plugin_grsai 文件夹

4. **放入新版插件**
- 将下载的 `nano_banana_plugin_grsai` 文件夹复制到上述目录

5. **重启字字动画软件**

## 🔄 更新建议

**强烈建议所有使用旧版非官方插件的用户更新至此官方版本**，以获得稳定的使用体验和持续的维护支持。

## 📞 反馈与支持

如遇到任何问题，请联系 GrsaiAPI 通过“在线联系客服”获取支持。
https://grsai.ai/dashboard/help

## 📝 更新日志

### v1.0.0（正式版）
- 重构请求接口，提升稳定性
- 新增全部 GrsaiAPI 画图模型支持
- 增加图片尺寸和分辨率选择功能
- 超时时间延长至 500 秒
- 修复原版“不出图”“模型无法使用”等问题

---

## 🔗 相关链接

- [GrsaiAPI 官方网站]（https://grsai.ai）
- [GrsaiAPI控制台](https://grsai.ai/dashboard)
- [GrsaiAPI APikey](https://grsai.ai/dashboard/api-keys)
- [问题反馈与技术支持](https://grsai.com/zh/dashboard/help)
