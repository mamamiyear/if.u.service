
import json
import logging
from typing import Protocol
import qiniu
import requests
from .config import get_instance as get_config


class OBS(Protocol):
    def Put(self, obs_path: str, content: bytes) -> str:
        """
        上传文件到OBS
        
        Args:
            obs_path (str): OBS目标路径
            content (bytes): 文件内容
        
        Returns:
            str: OBS文件路径
        """
        ...
    
    def Get(self, obs_path: str) -> bytes:
        """
        从OBS下载文件
        
        Args:
            obs_path (str): OBS文件路径
        
        Returns:
            bytes: 文件内容
        """
        ...
    
    def List(self, obs_path: str) -> list:
        """
        列出OBS目录下的所有文件
        
        Args:
            obs_path (str): OBS目录路径
        
        Returns:
            list: 所有文件路径列表
        """
        ...
    
    def Del(self, obs_path: str) -> bool:
        """
        删除OBS文件
        
        Args:
            obs_path (str): OBS文件路径
        
        Returns:
            bool: 是否删除成功
        """
        ...
    
    def Link(self, obs_path: str) -> str:
        """
        获取OBS文件链接
        
        Args:
            obs_path (str): OBS文件路径
        
        Returns:
            str: OBS文件链接
        """
        ...


class Koodo:
    def __init__(self):
        config = get_config()
        self.bucket_name = config.get('koodo_obs', 'bucket_name')
        self.prefix_path = config.get('koodo_obs', 'prefix_path')
        self.access_key = config.get('koodo_obs', 'access_key')
        self.secret_key = config.get('koodo_obs', 'secret_key')
        self.outer_domain = config.get('koodo_obs', 'outer_domain')
        self.auth = qiniu.Auth(self.access_key, self.secret_key)
        self.bucket = qiniu.BucketManager(self.auth)
        pass
    
    def Put(self, obs_path: str, content: bytes) -> str:
        """
        上传文件到OBS
        
        Args:
            obs_path (str): OBS目标路径
            content (bytes): 文件内容
        
        Returns:
            str: OBS文件路径
        """
        full_path = f"{self.prefix_path}{obs_path}"
        token = self.auth.upload_token(self.bucket_name, full_path)
        ret, info = qiniu.put_data(token, full_path, content)
        logging.debug(f"文件 {obs_path} 上传到 OBS, 结果: {ret}, 状态码: {info.status_code}, 错误信息: {info.text_body}")
        if ret is None or info.status_code != 200:
            logging.error(f"文件 {obs_path} 上传失败, 错误信息: {info.text_body}")
            return ""
        logging.info(f"文件 {obs_path} 上传成功, OBS路径: {full_path}")
        return f"{self.outer_domain}/{full_path}"

    def Get(self, obs_path: str) -> bytes:
        """
        从OBS下载文件
        
        Args:
            obs_path (str): OBS文件路径
        
        Returns:
            bytes: 文件内容
        """
        link = f"{self.outer_domain}/{self.prefix_path}{obs_path}"
        resp = requests.get(link)
        data = json.loads(resp.text)
        if 'error' in data and data['error']:
            logging.error(f"从 OBS {obs_path} 下载文件失败, 错误信息: {data['error']}")
            return None
        return resp.content
    
    def List(self, prefix: str = "") -> list[str]:
        """
        列出OBS目录下的所有文件
        
        Args:
            prefix (str, optional): OBS目录路径前缀. Defaults to "".
        
        Returns:
            list: 文件路径列表
        """
        prefix = f"{self.prefix_path}{prefix}"
        ret, eof, info = self.bucket.list(self.bucket_name, prefix)
        keys = []
        for item in ret['items']:
            item['key'] = item['key'].replace(prefix, "")
            keys.append(item['key'])
            # logging.debug(f"文件 {item['key']} 路径: {item['key']}")
        # logging.debug(f"ret: {ret}")
        # logging.debug(f"eof: {eof}")
        # logging.debug(f"info: {info}")
        return keys
    
    def Del(self, obs_path: str) -> bool:
        """
        删除OBS文件
        
        Args:
            obs_path (str): OBS文件路径
        
        Returns:
            bool: 是否删除成功
        """
        ret, info = self.bucket.delete(self.bucket_name, f"{self.prefix_path}{obs_path}")
        logging.debug(f"文件 {obs_path} 删除 OBS, 结果: {ret}, 状态码: {info.status_code}, 错误信息: {info.text_body}")
        if ret is None or info.status_code != 200:
            logging.error(f"文件 {obs_path} 删除 OBS 失败, 错误信息: {info.text_body}")
            return False
        logging.info(f"文件 {obs_path} 删除 OBS 成功")
        return True
    
    def Link(self, obs_path: str) -> str:
        """
        获取OBS文件链接
        
        Args:
            obs_path (str): OBS文件路径
        
        Returns:
            str: OBS文件链接
        """
        return f"{self.outer_domain}/{self.prefix_path}{obs_path}"


_obs_instance: OBS = None

def init():
    global _obs_instance
    _obs_instance = Koodo()

def get_instance() -> OBS:
    global _obs_instance
    return _obs_instance


if __name__ == "__main__":
    import os
    
    from .logger import init as init_logger
    init_logger(log_dir="logs", log_file="test", log_level=logging.INFO, console_log_level=logging.DEBUG)
    
    from .config import init as init_config, get_instance as get_config
    config_file = os.path.join(os.path.dirname(__file__), "../../configuration/test_conf.ini")
    init_config(config_file)
    
    init()
    obs = get_instance()
    
    # 从OBS下载测试图片
    # obs_path = "test111.PNG"
    # local_path = os.path.join(os.path.dirname(__file__), "../../test/9e03ad5eb8b1a51e752fb79cd8f98169.PNG")
    # content = None
    # with open(local_path, "rb") as f:
    #     content = f.read()
    # if content is None:
    #     print(f"文件 {local_path} 读取失败")
    #     exit(1)
    # obs.Put(obs_path, content)
    
    # link = obs.Link(obs_path)
    # print(f"文件 {obs_path} 链接: {link}")
    
    # 列出OBS目录下的所有文件
    keys = obs.List("")
    print(f"OBS 目录下的所有文件: {keys}")
    for key in keys:
        link = obs.Del(key)
        print(f"文件 {key} 删除 OBS 成功: {link}")
