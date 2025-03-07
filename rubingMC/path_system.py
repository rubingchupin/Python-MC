import os
import logging

class PathSystem:
    @staticmethod
    def ensure_dir(path: str) -> None:
        """确保目录存在"""
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            logging.info(f"创建目录: {path}")

    @classmethod
    def get_asset_path(cls, *subpaths: str) -> str:
        """获取有效的资源路径"""
        base_path = os.path.dirname(os.path.abspath(__file__))
        asset_path = os.path.join(base_path, '..', 'assets', *subpaths)
        cls.ensure_dir(os.path.dirname(asset_path))
        return asset_path