# WebHomeTV Android 5.0 (API 21) 适配构建

本仓库只存放**构建配方**，不存放 WebHomeTV 源码和二进制文件。GitHub Actions 运行时会克隆固定版本的上游源码，打上 Android 5.0 补丁后构建 APK。

## 工作流

- `.github/workflows/android5-python.yml` — **推荐**：Python 站源（爬虫源）可用。Chaquopy 15.0.1（最后一个官方支持 minSdk 21 的版本）+ Python 3.8 + AGP 8.5.2 + Gradle 8.7 + compileSdk 37。
- `.github/workflows/android5-fast.yml` — 快速包：禁用 Chaquopy，无 Python 爬虫源，native 沿用上游 API24 二进制。
- `.github/workflows/android5-native.yml` — native 全量重编到 API21，但仍禁用 Chaquopy。

## 爬虫源方案要点

Chaquopy 16 起强制 minSdk ≥ 24（因 API21/23 动态链接器与 Java 8 接口方法兼容问题），Chaquopy 15 是最后一个官方支持 API 21 的版本。为让它在上游工程上编译通过，补丁做了以下适配：

| 调整 | 原因 |
|---|---|
| AGP 9.2.1 → 8.5.2，Gradle 9.5.1 → 8.7 | Chaquopy 15 只兼容 AGP ≤8.5；Gradle 9 移除了它依赖的内部 API |
| Python 3.10 → 3.8，requirements 锁版本 | Chaquopy 仓库里只有 cp38 的 API16/21 wheel（lxml 4.6.3、ujson 1.35、pycryptodome 3.9.4 等） |
| platform-37 的 `AndroidVersion.ApiLevel=37.0` → `37` | AGP 8.5 无法解析带小数点的 ApiLevel |
| 关闭 AAR metadata 检查 | 部分 AndroidX 库声明 minAgpVersion 8.6+/8.9+，仅为构建期检查 |
| 排除重复 `META-INF/versions/9/OSGI-INF/MANIFEST.MF` | okhttp5 / bcprov jar 在 AGP 8.5 下触发重复资源错误 |
| `android.useAndroidX=true` | AGP 8.5 不再默认开启 |

构建产物中 Python 版 APK 比无 Python 版大约 13 MB，即 Chaquopy 运行时 + stdlib + 依赖包。

## 上游基准

- 仓库：`Silent1566/webhtv`
- Commit：`3f469e2fe51716c2068a13b9d48f61de34a89e0d`

## 产物

每条工作流构建完成后创建 pre-release，包含两个 leanback APK 和 `SHA256SUMS.txt`：

- `leanback-arm64_v8a.apk` — 64 位，现代智能电视 / 盒子
- `leanback-armeabi_v7a.apk` — 32 位，老款盒子

签名说明：仓库未配置发布 keystore，`app/build.gradle` 自动回退到 debug 签名，可直接侧载安装。

## 手动触发

在 GitHub 仓库 Actions 页面选择 `WebHomeTV Android 5.0 - Python Spiders (Chaquopy 15)`，点击 "Run workflow"。
