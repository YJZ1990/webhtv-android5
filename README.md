# WebHomeTV Android 5.0 (API 21) 适配构建

本仓库只存放**构建配方**，不存放 WebHomeTV 源码和二进制文件。GitHub Actions 运行时会克隆固定版本的上游源码，打上 Android 5.0 补丁后构建 APK。

## 文件说明

- `webhtv-android5.0.patch` — Android 5.0 适配补丁（11 个文件）：全局 minSdk 24 → 21，构建/校验脚本 API 24 → 21，native 锁定版本 24 → 21；**并包含恢复 Python 爬虫源所需的版本降级：AGP 9.2.1 → 8.5.2、Gradle 9.5.1 → 8.7、Chaquopy 17.0.0 → 15.0.1**。
- `chaquopy-disable.patch` — 旧版禁用 Chaquopy 的补丁（仅供 API21 快速验证使用）。**代价：Python 站源（.py）与 Python 字幕脚本不可用**。
- `.github/workflows/android5-python.yml` — **推荐工作流**：Chaquopy 15.0.1 官方支持 minSdk 21，Python 站源可用；AGP 8.5.2 + Gradle 8.7，native 沿用上游 API24 二进制。
- `.github/workflows/android5-fast.yml` — 快速出包：禁用 Chaquopy，native 沿用上游 API24 二进制（无爬虫源）。
- `.github/workflows/android5-native.yml` — 完整出包：MPV + EXO-ASS native 全量重编到 API21，但仍禁用 Chaquopy（无爬虫源）。

## 为什么选 Chaquopy 15

| Chaquopy | 最低 minSdk | 支持 AGP | 爬虫源 |
|---|---|---|---|
| 17.x | 24 | 9.0–9.5 | 支持但 API21 装不上 |
| 16.x | 24 | 8.6–8.13 | 支持但 API21 装不上 |
| **15.0.1** | **21** | **7.0–8.5** | **支持，API21 可用** |

因此恢复爬虫源的唯一官方支持路径是降级到 Chaquopy 15 + AGP 8.5，而不是硬绕过 17 的 minSdk 检查（16 提高门槛是因为 API23 以下动态链接器与 Java 8 接口方法存在真实兼容性问题，绕过会留下运行时隐患）。

## 上游基准

- 仓库：`Silent1566/webhtv`
- Commit：`3f469e2fe51716c2068a13b9d48f61de34a89e0d`

## 产物

每条工作流构建完成后会创建 pre-release，包含两个电视版 APK 和 `SHA256SUMS.txt`：

- `leanback-arm64_v8a.apk` — 64 位，现代智能电视 / 盒子
- `leanback-armeabi_v7a.apk` — 32 位，老款盒子

签名说明：仓库未配置发布 keystore，`app/build.gradle` 会自动回退到 debug 签名。可直接侧载安装，不能上架应用商店。

## 手动触发

在 GitHub 仓库 Actions 页面选择对应工作流，点击 "Run workflow"。
