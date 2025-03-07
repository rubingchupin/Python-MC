import numpy as np
from PIL import Image
from ursina import *
import noise
import logging
from rubingMC.path_system import PathSystem
from rubingMC.texture import TextureManager
class TerrainGenerator:
    def __init__(self, size: int):
        self.size = size
        self.scale = size / 3
        self.max_layers = 8
        self.base_layers = 2
        self.height_map = None
        self.texture_mgr = TextureManager()
        
        logging.info("初始化地形生成器")
        logging.info(f"参数：尺寸={size} 最大层数={self.max_layers} 基础层={self.base_layers}")

    def _generate_heightmap(self) -> np.ndarray:
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
            logging.info("地形高度图生成完成")
            return height_map
        except Exception as e:
            logging.error(f"地形高度图生成失败: {str(e)}")
            raise

    def _save_thumbnail(self) -> None:
        """保存地形缩略图"""
        try:
            thumbnail_path = PathSystem.get_asset_path('..\heightmap', 'heightmap.png')
            img_data = (self.height_map / self.max_layers * 255).astype(np.uint8)
            Image.fromarray(img_data, 'L').save(thumbnail_path)
            logging.info(f"地形缩略图已保存至: {thumbnail_path}")
        except Exception as e:
            logging.error(f"地形缩略图保存失败: {str(e)}")

    def build_terrain(self) -> Entity:
        """构建地形并保存数据"""
        try:
            self.height_map = self._generate_heightmap()
            self._save_thumbnail()
            
            logging.info("开始构建地形...")
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

    def _get_layer_material(self, current_layer: int, total_layers: int) -> str:
        if current_layer < 2:
            return 'stone'
        if current_layer == total_layers - 1:
            height_ratio = (total_layers - 2) / self.max_layers
            return 'snow' if height_ratio > 0.8 else 'stone' if height_ratio > 0.6 else 'grass'
        return 'dirt'

    def _create_block(self, parent: Entity, position: tuple, material: str) -> None:
        try:
            # 关键修改：分离获取纹理和颜色
            tex = self.texture_mgr.textures.get(material)
            col = self.texture_mgr.color_map.get(material, color.white)
            block_color = color.white if tex is not None else col
            Entity(
                parent=parent,
                model='cube',
                texture=tex,  # 只接受纹理对象或None
                color=block_color,    # 单独设置颜色
                position=position,
                collider='box'
            )
        except Exception as e:
            logging.warning(f"方块创建失败: {position} - {str(e)}")