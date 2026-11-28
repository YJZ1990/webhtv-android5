# WebHomeTV Android 5.0 (API 21) 适配构建

本仓库只存放**构建配方**，不存放 WebHomeTV 源码和二进制文件。GitHub Actions 运行时克隆固定版本的上游源码，打上 Android 5.0 补丁后构建 APK。

## 工作流

| 工作流 | 用途 | 说明 |
|---|---|---|
| `.github/workflows/android5-native.yml` | **主用** | 用 NDK 把所有 `api>21` 的原生栈重编到 API 21，再出包。默认由 `webhtv-android5.0.patch` 变更触发 |
| `.github/workflows/android5-python.yml` | 备用 | 只用上游预编译 `.so` 出包（ASS/media3ext/dovi 仍为 24/23/26），验证 Chaquopy 15 链路 |

工具链组合：Chaquopy 15.0.1 + Python 3.8 + AGP 8.5.2 + Gradle 8.7 + compileSdk 37 + minSdk 21 + NDK 29.0.14206865。

## 最新产物

Release：`android5-native-202611280952`（run [46092721074](https://github.com/YJZ1990/webhtv-android5/actions/runs/46092721074)，success）

| 文件 | 大小 (字节) | SHA256 |
|---|---|---|
| `leanback-arm64_v8a.apk` | 91,030,719 | `8e7b3260f8f4476ca8c47705d24a872ed070dedfbc5be9e9c8b88be1809f03b8` |
| `leanback-armeabi_v7a.apk` | 85,163,750 | `77d5cbea9bb4172f48e2ffb8b41d604de6f4b37d26a1f9e80c1d810438ce5832` |

已核验项（本地解析 APK 实测，非构建日志转述）：

| 检查 | arm64-v8a | armeabi-v7a |
|---|---|---|
| `minSdkVersion` / `targetSdkVersion` / `compileSdkVersion` | 21 / 28 / 37 | 21 / 28 / 37 |
| `versionName` / `versionCode` | 5.6.0 / 560 | 5.6.0 / 560 |
| api21 原生库数量 | 46 | 44 |
| `libexo_ass.so`（ASS 字幕） | **api 21**（原 24） | 不打包（arm64 专用） |
| `libmedia3ext.so` | **api 21**（原 23） | **api 21**（原 23） |
| `libplayer.so` / mpv 栈 10 库 | **api 21**（原 24） | **api 21**（原 24） |
| `libexo_dovi_renderer.so` | api 26（保持，运行时门控） | api 26（保持，运行时门控） |
| Python 运行时 | `libpython3.8.so` + `assets/chaquopy/app.imy` 在位 | 同左 |

## native 重编记录（本轮）

四个原生栈的 API 级别来源各不相同，逐个处理：

| 栈 | 原 API | 处理方式 |
|---|---|---|
| mpv 全栈（`assets/mpv-libs/*`，10 个库） | 24 | `build_mpv_native.sh` 的 `android_api` 默认值 24→21，NDK 29 源码重编（1490 个对象） |
| `libplayer.so`（mpv JNI 桥） | 24 | **三不管文件**：`build_mpv_native.sh` 明确保留仓库预编译件，Gradle 的 `externalNativeBuild` 只编 `exo_dovi_renderer`。改为在 mpv 阶段执行 `build_mpv_player_jni.sh --abi all --install` 从源码重链 |
| `libexo_ass.so`（ASS 字幕） | 24 | `build_exo_ass_native.py` 的 meson cross 文件从 lock 的 `api` 派生工具链三元组（原写死 `android24-clang`） |
| `libmedia3ext.so` | 23 | nextlib `media3ext/build.gradle.kts` minSdk 23→21 + 补丁系列修复后重编 |

**关键坑：依赖编译 API 与最终链接 API 必须一致。** `build_exo_ass_native.py` 原来用 `aarch64-linux-android24-clang` 编依赖（freetype/fontconfig/libxml2/harfbuzz/libass），却按 `ANDROID_PLATFORM=android-21` 链接 `libexo_ass.so`。NDK 头文件按 `__ANDROID_API__` 分支：

- API ≥ 23：`stdout`/`stderr` 是真正的 `extern FILE*`，`strerror_r` 解析到 `__gnu_strerror_r`，有 `mkostemp`
- API < 23：`stdout` 是 `(&__sF[1])` 宏，走 posix `strerror_r`，无 `mkostemp`

于是链接报 4 个未定义符号：`stdout`、`stderr`、`mkostemp`、`__gnu_strerror_r`。修复后依赖与最终 `.so` 都在 API 21 编译，符号自然对齐。

另外 `third_party/mpv-player-jni/src/main.cpp` 的 `pthread_setname_np` 是 API 26+，在 `-Werror` 下编译失败，已改为按 `__ANDROID_API__ >= 26` 条件编译（纯调试用途）。

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

## 已知限制（均为上游既有设计，非本轮引入）

| 项 | 现状 | 影响 |
|---|---|---|
| `libexo_dovi_renderer.so` = api26 | `ExoDv5Native.loadLibrary()` 有 `SDK_INT < 26` 提前 return，Android 5 上不会 `dlopen`；其内部用 `AHardwareBuffer`/`AImageReader`（NDK 24/26 引入），物理上无法编到 21 | Dolby Vision 仅在 Android 8.0+ 可用，低版本走 HDR10 基础路径，不崩 |
| mpv 栈强引用 `vkCreateSamplerYcbcrConversion` 等 Vulkan 1.1 符号 | 依赖系统 `libvulkan.so`（Android 7.0+）。Android 5/6 无此库 | `MPVLib.ensureLoaded()` 整体 try/catch，失败返回 false，播放器回退到 Exo/IJK，不崩 |
| `assets/lab/proot/libandroid-shmem.so` = api24 | proot 沙箱内的辅助库 | 仅影响 lab/proot 终端实验功能 |
| `libmitv.so`/`libjpa.so`/`libxl_stat.so` 等 | 第三方 blob，无 Android note | 与 API 级别检查无关（本来就没有） |
| FFmpeg 系库弱引用 `memfd_create`（API 30）、libc++ 弱引用 `__cxa_thread_atexit_impl` | 弱符号，缺失时为 NULL，运行时自动降级 | 无影响。工作流内"未解析符号"报告只看强引用 |
| 未配置发布 keystore | `app/build.gradle` 自动回退 debug 签名 | 可直接侧载；覆盖安装需先卸载其他签名的同包名版本 |

## 上游基准

- 仓库：`Silent1566/webhtv`
- Commit：`3f469e2fe51716c2068a13b9d48f61de34a89e0d`

## 改用无 Python 版本

若不想要 Chaquopy，可从补丁里去掉 `chaquo/build.gradle` 的 `com.chaquo.python` 插件与 `chaquo` 模块依赖，并把 `gradle/libs.versions.toml` 的 `python` 版本行删掉；此时 APK 约小 13 MB，但 Python 站源与 Python 字幕脚本不可用。

## 手动触发

在 GitHub 仓库 Actions 页面选择 `WebHomeTV Android 5.0 - Native API21 Rebuild`，点击 "Run workflow"。
