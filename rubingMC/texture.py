from ursina import *
from rubingMC.path_system import PathSystem
import logging
import os

class TextureManager:
    def __init__(self):
        self.color_map = {
            'snow': color.rgba(1.0, 0.98, 0.98, 1.0),  # (255,250,250) → 归一化
            'stone': color.rgba(0.5, 0.5, 0.5, 1.0),    # (128,128,128) → 0.5
            'grass': color.rgba(0.133, 0.545, 0.133, 1.0),  # (34,139,34)
            'dirt': color.rgba(0.545, 0.27, 0.075, 1.0),     # (139,69,19)
        }
        self.textures = {}
        self._load_textures()

    def _load_textures(self) -> None:
        logging.info("加载纹理资源...")
        for name in self.color_map.keys():
            try:
                tex_path = PathSystem.get_asset_path('textures', f'{name}.png')
                # 修正为绝对路径检查
                if tex_path and os.path.exists(tex_path):
                    self.textures[name] = load_texture(tex_path)
                    logging.info(f"成功加载: {name}.png")
                else:
                    logging.warning(f"缺失纹理文件: {name}.png")
                    self.textures[name] = None
            except Exception as e:
                logging.error(f"纹理加载错误: {name} - {str(e)}")
                self.textures[name] = None