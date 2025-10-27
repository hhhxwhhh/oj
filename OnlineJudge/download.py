"""
NLTK数据下载脚本
此脚本用于在当前目录下载NLTK所需的语料库数据
"""

import nltk
import os
import sys
import ssl

def download_nltk_data():
    """
    在当前目录下载NLTK数据，处理SSL证书问题
    """
    print("开始在当前目录下载NLTK数据...")
    
    # 处理SSL证书问题
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    
    # 定义需要下载的数据包
    packages = ['punkt', 'stopwords']
    
    # 设置当前目录为下载目录
    current_dir = os.getcwd()
    nltk_data_dir = os.path.join(current_dir, "nltk_data")
    
    # 确保nltk_data目录存在
    os.makedirs(nltk_data_dir, exist_ok=True)
    
    # 设置NLTK数据路径
    if nltk_data_dir not in nltk.data.path:
        nltk.data.path.append(nltk_data_dir)
    
    print(f"NLTK数据将被下载到: {nltk_data_dir}")
    
    success_count = 0
    for package in packages:
        try:
            print(f"正在下载 {package}...")
            nltk.download(package, download_dir=nltk_data_dir)
            print(f"✓ {package} 下载成功")
            success_count += 1
        except Exception as e:
            print(f"✗ {package} 下载失败: {str(e)}")
    
    print(f"\n下载完成 ({success_count}/{len(packages)} 成功)")
    
    # 验证下载
    print("\n验证数据...")
    verification_success = True
    for package in packages:
        try:
            if package == 'punkt':
                nltk.data.find('tokenizers/punkt')
            elif package == 'stopwords':
                nltk.data.find('corpora/stopwords')
            print(f"✓ {package} 验证成功")
        except LookupError:
            print(f"✗ {package} 验证失败")
            verification_success = False
    
    if verification_success:
        print("\n所有NLTK数据已成功下载并验证!")
        print(f"数据位置: {nltk_data_dir}")
        return True
    else:
        print("\n部分数据下载或验证失败，请检查网络连接后重试")
        return False

if __name__ == "__main__":
    try:
        success = download_nltk_data()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n操作已被用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生未预期的错误: {str(e)}")
        sys.exit(1)