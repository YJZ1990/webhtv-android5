# WebHomeTV Android 5.0 (API 21) 适配构建

本仓库只存放**构建配方**，不存放 WebHomeTV 源码和二进制文件。GitHub Actions 运行时克隆固定版本的上游源码，打上 Android 5.0 补丁后构建 APK。

## 工作流

唯一工作流：`.github/workflows/android5-python.yml` — **爬虫源（Python 站源）可用**。

工具链组合：Chaquopy 15.0.1 + Python 3.8 + AGP 8.5.2 + Gradle 8.7 + compileSdk 37 + minSdk 21。

## 最新产物

Release：`android5-python-202611272156`（run [46009672718](https://github.com/YJZ1990/webhtv-android5/actions/runs/46009672718)，success）

| 文件 | 大小 (字节) | SHA256 |
|---|---|---|
| `leanback-arm64_v8a.apk` | 90,986,080 | `f26775b905f2ea1972678c34d57194909fc878e0f84c7adce3ee921ab74b3e37` |
| `leanback-armeabi_v7a.apk` | 85,112,975 | `5207fc6c24ef748667bd14e061e599f6a3c24ff84ea8e2759eb385f3e1f27870` |

已核验项：

| 检查 | 结果 |
|---|---|
| `uses-sdk minSdkVersion` | 21（两个 APK 均如此） |
| `targetSdkVersion` / `compileSdkVersion` | 28 / 37 |
| Python 运行时 | `libpython3.8.so`、`libchaquopy_java.so` 已打包 |
| Python 依赖 | lxml 4.6.3、pyquery 1.4.3、requests 2.31.0、beautifulsoup4 4.12.3、ujson 1.35、pycryptodome 3.9.4 全部在位 |
| 爬虫入口 | `assets/chaquopy/app.imy` 含 `app.py`、`runner.py`、`trigger.py`、`base/spider.py` |
| native 库 API 级别 | 25 个库为 api21；`libexo_ass.so`=24、`libmedia3ext.so`=23、`libexo_dovi_renderer.so`=26 |

## 爬虫源方案要点

Chaquopy 16 起强制 minSdk ≥ 24（官方原因是 API21/23 动态链接器与 Java 8 接口方法兼容问题），Chaquopy 15 是最后一个官方支持 API 21 的版本。为让它在上游工程上编译通过，补丁做了以下适配：

| 调整 | 原因 |
|---|---|
| AGP 9.2.1 → 8.5.2，Gradle 9.5.1 → 8.7 | Chaquopy 15 只兼容 AGP ≤8.5；Gradle 9 移除了它依赖的内部 API（`VersionNumber`、`DeprecateType`） |
| Python 3.10 → 3.8，requirements 锁版本 | Chaquopy 仓库里只有 cp38 的 API16/21 wheel（lxml 4.6.3、ujson 1.35、pycryptodome 3.9.4 等） |
| platform-37 的 `AndroidVersion.ApiLevel=37.0` → `37` | AGP 8.5 无法解析带小数点的 ApiLevel，会误判 platform 缺失 |
| 关闭 AAR metadata 检查 | 部分 AndroidX 库声明 minAgpVersion 8.6+/8.9+，仅为构建期检查，不影响运行时 |
| 排除重复 `META-INF/versions/9/OSGI-INF/MANIFEST.MF` | okhttp5 / bcprov jar 在 AGP 8.5 下触发重复资源错误 |
| `android.useAndroidX=true` | AGP 8.5 不再默认开启 |
| manifest 注入 `tools:overrideLibrary` | 可选 AAR（tvbus / thunder / hook / media3 等）声明 minSdk 24，仅在低版本设备上不加载 |

构建产物中 Python 版 APK 比无 Python 版大约 13 MB，即 Chaquopy 运行时 + stdlib + 依赖包。

## 已知限制

- `libexo_ass.so`(api24)、`libmedia3ext.so`(api23)、`libexo_dovi_renderer.so`(api26) 沿用上游预编译产物。Android 5.0 设备上 ASS 特效字幕、Dolby Vision 渲染可能加载失败并降级（普通字幕/播放不受影响）。
- 如需把这几个库也降到 api21，需用 NDK 重编对应 native 模块。
- 未配置发布 keystore，`app/build.gradle` 自动回退 debug 签名，可直接侧载；覆盖安装需先卸载其他签名的同包名版本。

## 上游基准

- 仓库：`Silent1566/webhtv`
- Commit：`3f469e2fe51716c2068a13b9d48f61de34a89e0d`

## 改用无 Python 版本

若不想要 Chaquopy，可从 `android5-python` 的补丁里去掉 `chaquo/build.gradle` 的 `com.chaquo.python` 插件与 `chaquo` 模块依赖，并把 `gradle/libs.versions.toml` 的 `python` 版本行删掉；此时 APK 约小 13 MB，但 Python 站源与 Python 字幕脚本不可用。

## 手动触发

在 GitHub 仓库 Actions 页面选择 `WebHomeTV Android 5.0 - Python Spiders (Chaquopy 15)`，点击 "Run workflow"。
