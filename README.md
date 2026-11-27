# WebHomeTV Android 5.0 (API 21) 适配构建

本仓库只存放**构建配方**，不存放 WebHomeTV 源码和二进制文件。GitHub Actions 运行时会克隆固定版本的上游源码，打上 Android 5.0 补丁后构建 APK。

## 文件说明

- `webhtv-android5.0.patch` — Android 5.0 适配补丁（10 个文件，13 增 13 删）
- `chaquopy-disable.patch` — 禁用 Chaquopy Python 运行时（5 个文件，34 增 406 删）。Chaquopy 17 强制 minSdk≥24，支持 API 21 的 15.0 与项目 AGP 9.2 不兼容，因此用编译安全的空实现替换。**代价：Python 站源（.py）与 Python 字幕脚本不可用**；直播/点播/EPG/MPV 播放/JS 源/离线缓存/ASS 字幕全部保留。
  - 全局 `minSdk 24 → 21`
  - cmake platform `android-26 → android-21`
  - MPV / EXO-ASS / DVD native 锁定版本 `api 24 → 21`
  - 构建与校验脚本的硬编码 API 24 全部改为 21
- `.github/workflows/android5-fast.yml` — 快速出包：直接构建 leanback Release APK（自动 debug 签名），原生库沿用上游 API 24 二进制
- `.github/workflows/android5-native.yml` — 完整出包：先把 MPV + EXO-ASS native 全量重编到 API 21，再构建 leanback Release APK

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
