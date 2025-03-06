import os
import sys
import logging
import random
import numpy as np
from PIL import Image
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import noise

# 配置日志系统
log_path = os.path.join(os.getcwd(), 'terrain_gen.log')
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)
logging.info("=== 地形生成器启动 ===")

# 获取用户输入
try:
    MAP_SIZE = int(input("请输入地形尺寸（32-256）: ")) or 64
    MAP_SIZE = max(32, min(256, MAP_SIZE))
except ValueError:
    logging.warning("输入无效，使用默认尺寸64")
    MAP_SIZE = 64

class PathSystem:
    @staticmethod
    def ensure_dir(path):
        """确保目录存在"""
        if not os.path.exists(path):
            os.makedirs(path)
            logging.info(f"创建目录: {path}")

    @classmethod
    def get_asset_path(cls, *subpaths):
        """获取有效的资源路径"""
        base_path = os.path.dirname(os.path.abspath(__file__))
        asset_path = os.path.join(base_path, 'assets', *subpaths)
        cls.ensure_dir(os.path.dirname(asset_path))
        return asset_path

class TerrainGenerator:
    def __init__(self, size):
        self.size = size
        self.scale = size / 3
        self.max_layers = 8
        self.base_layers = 2
        self.height_map = None
        self.texture_mgr = TextureManager()
        
        logging.info("初始化地形生成器")
        logging.info(f"参数：尺寸={size} 最大层数={self.max_layers} 基础层={self.base_layers}")

    def _generate_heightmap(self):
        """生成离散高度图"""
        logging.info("开始生成高度图...")
        height_map = np.zeros((self.size, self.size), dtype=int)
        
        try:
            for x in range(self.size):
                for z in range(self.size):
                    noise_val = noise.pnoise2(
                        x/self.scale, z/self.scale,
                        octaves=5, persistence=0.5, lacunarity=2.0
                    )
                    height_map[x][z] = max(
                        self.base_layers,
                        int(round((noise_val + 1) * self.max_layers / 2))
                    )
            logging.info("高度图生成完成")
            return height_map
        except Exception as e:
            logging.error(f"高度图生成失败: {str(e)}")
            raise

    def _save_thumbnail(self):
        """保存地形缩略图"""
        try:
            thumbnail_path = PathSystem.get_asset_path('thumbnails', 'heightmap.png')
            img_data = (self.height_map / self.max_layers * 255).astype(np.uint8)
            Image.fromarray(img_data, 'L').save(thumbnail_path)
            logging.info(f"缩略图已保存至: {thumbnail_path}")
        except Exception as e:
            logging.error(f"缩略图保存失败: {str(e)}")

    def build_terrain(self):
        """构建地形并保存数据"""
        try:
            self.height_map = self._generate_heightmap()
            self._save_thumbnail()
            
            logging.info("开始构建地形网格...")
            terrain = Entity()
            half_size = self.size // 2
            
            for x in range(self.size):
                for z in range(self.size):
                    layers = self.height_map[x][z]
                    for y in range(layers):
                        material = self._get_layer_material(y, layers)
                        self._create_block(terrain, (x-half_size, y, z-half_size), material)
            
            logging.info("地形构建完成")
            return terrain
        except Exception as e:
            logging.critical(f"地形构建失败: {str(e)}")
            raise

    def _get_layer_material(self, current_layer, total_layers):
        if current_layer < 2:
            return 'stone'
        if current_layer == total_layers - 1:
            height_ratio = (total_layers - 2) / self.max_layers
            return 'snow' if height_ratio > 0.8 else 'stone' if height_ratio > 0.6 else 'grass'
        return 'dirt'

    def _create_block(self, parent, position, material):
        try:
            Entity(
                parent=parent,
                model='cube',
                texture=self.texture_mgr.get_material(material),
                position=position,
                color=self.texture_mgr.color_map[material],
                collider='box'
            )
        except Exception as e:
            logging.warning(f"方块创建失败: {position} - {str(e)}")

class TextureManager:
    def __init__(self):
        self.color_map = {
            'snow': color.rgb(255, 250, 250),
            'stone': color.rgb(128, 128, 128),
            'grass': color.rgb(34, 139, 34),
            'dirt': color.rgb(139, 69, 19)
        }
        self.textures = {}
        self._load_textures()

    def _load_textures(self):
        logging.info("加载纹理资源...")
        for name in self.color_map.keys():
            try:
                tex_path = PathSystem.get_asset_path('textures', f'{name}.png')
                if os.path.exists(tex_path):
                    self.textures[name] = load_texture(tex_path)
                    logging.info(f"成功加载: {name}.png")
                else:
                    logging.warning(f"缺失纹理: {name}.png")
            except Exception as e:
                logging.error(f"纹理加载错误: {name} - {str(e)}")

    def get_material(self, name):
        return self.textures.get(name, self.color_map[name])

if __name__ == '__main__':
    app = Ursina()
    window.title = f"分层地形生成 - {MAP_SIZE}x{MAP_SIZE}"
    window.size = (1600, 900)
    
    try:
        generator = TerrainGenerator(MAP_SIZE)
        terrain = generator.build_terrain()
        terrain.y = -1
        
        player = FirstPersonController(position=(0, 50, 0))
        player.speed = 15
        player.gravity = 1.0
        
        Sky(color=color.rgb(135, 206, 250))
        DirectionalLight().look_at(Vec3(1, -1, 0.5))
        
        app.run()
    except Exception as e:
        logging.critical(f"致命错误: {str(e)}")
        input("按回车键退出...")