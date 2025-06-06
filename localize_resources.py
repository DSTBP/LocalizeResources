import os
import re
import requests
import urllib.parse
from bs4 import BeautifulSoup
from pathlib import Path
import hashlib
import base64
import mimetypes
import shutil
from loguru import logger
from datetime import datetime
import chardet
import gzip
import brotli

class ResourceLocalizer:
    def __init__(self, base_dir, proxy=None):
        self.base_dir = Path(base_dir)
        self.output_dir = self.base_dir.parent / f"{self.base_dir.name}_localized_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.static_dir = self.output_dir / 'static'
        self.css_dir = self.static_dir / 'css'
        self.js_dir = self.static_dir / 'js'
        self.fonts_dir = self.css_dir / 'fonts'
        self.images_dir = self.static_dir / 'images'
        self.proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'} if proxy else None
        
        # 创建必要的目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.css_dir.mkdir(parents=True, exist_ok=True)
        self.js_dir.mkdir(parents=True, exist_ok=True)
        self.fonts_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # 用于跟踪已下载的文件
        self.downloaded_files = {}
        
        # 添加字体文件的MIME类型
        mimetypes.add_type('application/font-woff', '.woff')
        mimetypes.add_type('application/font-woff2', '.woff2')
        mimetypes.add_type('application/x-font-ttf', '.ttf')
        mimetypes.add_type('application/vnd.ms-fontobject', '.eot')
        
        self.check_cancel = lambda: True  # 添加默认的检查函数
        
        logger.info(f"初始化完成，输出目录: {self.output_dir}")

    def get_file_hash(self, content):
        return hashlib.md5(content).hexdigest()[:8]

    def process_data_url(self, data_url):
        """处理data URL格式的资源"""
        try:
            # 提取data URL的MIME类型和数据
            match = re.match(r'data:([^;]+);base64,(.+)', data_url)
            if not match:
                # 如果不是base64编码的data URL，尝试直接提取数据
                match = re.match(r'data:([^,]+),(.+)', data_url)
                if not match:
                    return None
            
            mime_type, data = match.groups()
            logger.debug(f"处理data URL: {mime_type}")
            
            # 根据MIME类型确定文件扩展名
            ext_map = {
                'image/svg+xml': '.svg',
                'image/png': '.png',
                'image/jpeg': '.jpg',
                'image/gif': '.gif',
                'image/webp': '.webp',
                'image/x-icon': '.ico',
                'application/font-woff': '.woff',
                'application/font-woff2': '.woff2',
                'application/x-font-ttf': '.ttf',
                'application/vnd.ms-fontobject': '.eot'
            }
            
            ext = ext_map.get(mime_type, '.bin')
            
            # 如果是base64编码，解码数据
            if 'base64' in data_url:
                content = base64.b64decode(data)
            else:
                # 对于非base64编码的数据，进行URL解码
                content = urllib.parse.unquote(data).encode('utf-8')
            
            # 生成文件名
            filename = f"data_url_{self.get_file_hash(content)}{ext}"
            logger.debug(f"生成data URL文件名: {filename}")
            return content, filename
        except Exception as e:
            logger.error(f"处理data URL失败: {str(e)}")
            return None

    def decompress_content(self, content, content_encoding):
        """解压缩内容"""
        try:
            if content_encoding == 'gzip':
                return gzip.decompress(content)
            elif content_encoding == 'br':
                return brotli.decompress(content)
            return content
        except Exception as e:
            logger.error(f"解压缩失败: {str(e)}")
            return content

    def download_file(self, url):
        try:
            # 检查是否是data URL
            if url.startswith('data:'):
                result = self.process_data_url(url)
                if result:
                    return result[0]
                return None
            
            # 设置请求头，模拟浏览器请求
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            logger.info(f"开始下载: {url}")
            
            # 允许重定向
            session = requests.Session()
            session.max_redirects = 5
            response = session.get(url, proxies=self.proxies, headers=headers, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            # 检查Content-Type
            content_type = response.headers.get('Content-Type', '')
            if 'font' in content_type or any(ext in url.lower() for ext in ['.woff', '.woff2', '.ttf', '.eot']):
                logger.info(f"下载字体文件: {url}")
            
            # 获取最终URL（处理重定向后）
            final_url = response.url
            if final_url != url:
                logger.info(f"URL重定向: {url} -> {final_url}")
            
            # 获取内容编码
            content_encoding = response.headers.get('Content-Encoding', '')
            content = response.content
            
            # 解压缩内容
            if content_encoding:
                logger.info(f"检测到压缩内容: {content_encoding}")
                content = self.decompress_content(content, content_encoding)
            
            logger.success(f"下载成功: {final_url}")
            return content
        except Exception as e:
            logger.error(f"下载失败 {url}: {str(e)}")
            return None

    def decode_content(self, content, url):
        """智能解码内容"""
        try:
            # 尝试UTF-8解码
            return content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                # 使用chardet检测编码
                detected = chardet.detect(content)
                encoding = detected['encoding']
                if encoding:
                    logger.info(f"检测到编码 {encoding} 用于 {url}")
                    return content.decode(encoding)
                else:
                    # 如果无法检测编码，尝试其他常见编码
                    for encoding in ['latin1', 'iso-8859-1', 'gbk', 'gb2312']:
                        try:
                            return content.decode(encoding)
                        except UnicodeDecodeError:
                            continue
                    raise
            except Exception as e:
                logger.error(f"解码失败 {url}: {str(e)}")
                # 如果所有解码都失败，返回原始内容
                return content

    def process_css_content(self, css_content, css_url):
        """处理CSS内容中的相对路径资源"""
        logger.info(f"处理CSS文件: {css_url}")
        # 提取CSS中的url引用
        url_pattern = r'url\([\'"]?(.*?)[\'"]?\)'
        base_url = urllib.parse.urljoin(css_url, '.')
        
        def replace_url(match):
            url = match.group(1)
            if url.startswith('data:'):
                # 处理data URL
                result = self.process_data_url(url)
                if result:
                    content, filename = result
                    self.save_file(content, f"data_url_{filename}", 'images')
                    return f'url("./images/{filename}")'
                return match.group(0)
            
            if url.startswith(('http://', 'https://')):
                return match.group(0)
            
            # 处理相对路径
            full_url = urllib.parse.urljoin(base_url, url)
            content = self.download_file(full_url)
            if not content:
                return match.group(0)
            
            # 根据文件类型保存到相应目录
            if any(ext in url.lower() for ext in ['.woff', '.woff2', '.ttf', '.eot']):
                filename = self.save_file(content, full_url, 'fonts')
                return f'url("./fonts/{filename}")'
            elif any(ext in url.lower() for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico']):
                filename = self.save_file(content, full_url, 'images')
                return f'url("./images/{filename}")'
            else:
                return match.group(0)
        
        return re.sub(url_pattern, replace_url, css_content)

    def save_file(self, content, original_url, file_type):
        # 从URL中提取文件名
        if isinstance(original_url, str):
            filename = os.path.basename(urllib.parse.urlparse(original_url).path)
            if not filename:
                filename = f"file_{self.get_file_hash(content)}.{file_type}"
        else:
            filename = original_url
        
        # 处理版本号
        if isinstance(original_url, str):
            version_match = re.search(r'@([\d.]+)', original_url)
            if version_match:
                version = version_match.group(1)
                name, ext = os.path.splitext(filename)
                filename = f"{name}_v{version}{ext}"
        
        # 检查文件是否已存在
        if filename in self.downloaded_files:
            if self.downloaded_files[filename] == self.get_file_hash(content):
                logger.debug(f"文件已存在，跳过: {filename}")
                return filename
            else:
                # 如果内容不同，添加哈希后缀
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{self.get_file_hash(content)}{ext}"
        
        # 根据文件类型选择保存目录
        if file_type == 'css':
            save_path = self.css_dir / filename
        elif file_type == 'js':
            save_path = self.js_dir / filename
        elif file_type == 'fonts':
            save_path = self.fonts_dir / filename
        elif file_type == 'images':
            save_path = self.images_dir / filename
        else:
            save_path = self.static_dir / filename
        
        with open(save_path, 'wb') as f:
            f.write(content)
        
        self.downloaded_files[filename] = self.get_file_hash(content)
        logger.info(f"保存文件: {save_path}")
        return filename

    def process_html_file(self, html_file):
        # 检查是否取消
        if not self.check_cancel():
            return
            
        logger.info(f"处理HTML文件: {html_file}")
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        modified = False

        # 处理CSS链接
        for link in soup.find_all('link', rel='stylesheet'):
            if link.get('href') and not link['href'].startswith(('http://', 'https://')):
                continue
            
            url = link['href']
            content = self.download_file(url)
            if content:
                # 处理CSS内容中的相对路径资源
                decoded_content = self.decode_content(content, url)
                processed_content = self.process_css_content(decoded_content, url)
                filename = self.save_file(processed_content.encode('utf-8'), url, 'css')
                link['href'] = f'./static/css/{filename}'
                modified = True

        # 处理JS脚本
        for script in soup.find_all('script', src=True):
            if not script['src'].startswith(('http://', 'https://')):
                continue
            
            url = script['src']
            content = self.download_file(url)
            if content:
                filename = self.save_file(content, url, 'js')
                script['src'] = f'./static/js/{filename}'
                modified = True

        if modified:
            # 创建输出目录结构
            relative_path = html_file.relative_to(self.base_dir)
            output_path = self.output_dir / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            logger.success(f"保存修改后的HTML文件: {output_path}")

    def process_directory(self):
        logger.info(f"开始处理目录: {self.base_dir}")
        for root, _, files in os.walk(self.base_dir):
            # 检查是否取消
            if not self.check_cancel():
                return
                
            for file in files:
                # 检查是否取消
                if not self.check_cancel():
                    return
                    
                if file.endswith('.html'):
                    html_path = Path(root) / file
                    self.process_html_file(html_path)
                else:
                    # 复制非HTML文件
                    relative_path = Path(root).relative_to(self.base_dir)
                    output_path = self.output_dir / relative_path / file
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(Path(root) / file, output_path)
                    logger.debug(f"复制文件: {output_path}")
        
        logger.success(f"处理完成，输出目录: {self.output_dir}")

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
    # base_dir = input("请输入要处理的目录路径: ")
    base_dir = r"C:\Users\r0xanne\Desktop\111\UI"
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