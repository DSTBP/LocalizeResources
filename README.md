# Resource Localizer

## 概述

`ResourceLocalizer` 是一个 Python 脚本，用于将 HTML 项目中的外部资源（如 CSS、JavaScript、字体和图片）本地化。它会下载这些资源并将其保存到本地目录，同时更新 HTML 文件中的引用路径，确保项目可以在没有网络连接的情况下正常运行。

## 功能特性

- **资源下载**：支持下载 CSS、JavaScript、字体和图片资源。
- **数据 URL 处理**：能够处理 `data:` URL 格式的资源。
- **内容解压缩**：自动解压缩 `gzip` 和 `brotli` 压缩的内容。
- **编码检测**：智能检测和处理不同编码的文件内容。
- **文件重命名**：根据文件内容生成唯一的文件名，避免冲突。
- **目录结构保留**：处理后的文件会保留原始目录结构。

## 安装依赖

在运行脚本之前，需要安装必要的 Python 库。可以使用以下命令进行安装：

```
pip install requests beautifulsoup4 loguru chardet brotli
```



## 使用方法

### 配置脚本

在 `main` 函数中，可以配置基础目录和代理设置：

```python
def main():
    # 配置日志
    logger.remove()
    logger.add(
        "localize_resources.log",
        rotation="10 MB",
        retention="1 week",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    logger.add(lambda msg: print(msg), level="INFO")
    
    # 设置基础目录和代理
    base_dir = r"C:\Users\r0xanne\Desktop\111\UI"  # 要处理的目录路径
    proxy = "127.0.0.1:7890"  # 设置代理
    
    try:
        localizer = ResourceLocalizer(base_dir, proxy)
        localizer.process_directory()
        logger.success("资源本地化完成！")
    except Exception as e:
        logger.error(f"处理过程中发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    main()
```

### 运行脚本

将上述代码保存为 localize_resources.py，然后在终端中运行以下命令：

```bash
python localize_resources.py
```

## 脚本参数

- **`base_dir`**：要处理的项目目录路径。
- **`proxy`**：可选参数，用于设置代理服务器。格式为 `ip:port`。

## 输出目录

处理后的文件会保存到一个新的目录中，目录名格式为 `{base_dir_name}_localized_{YYYYMMDD_HHMMSS}`，其中 `{base_dir_name}` 是原始目录名，`{YYYYMMDD_HHMMSS}` 是处理时间。

## 日志记录

脚本会将处理过程中的信息记录到 `localize_resources.log` 文件中，同时也会在终端输出信息。日志文件会按照 10MB 的大小进行分割，保留一周的日志记录。

## 注意事项

- 请确保有足够的磁盘空间来保存下载的资源。
- 如果使用代理，请确保代理服务器正常工作。
- 脚本会处理所有 HTML 文件中的外部资源引用，但不会处理内联资源。

## 贡献

如果你发现任何问题或有改进建议，请在 GitHub 上提交 issue 或 pull request。

## 许可证

本项目采用 [MIT 许可证](https://opensource.org/licenses/MIT)。