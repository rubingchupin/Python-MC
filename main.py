import os
import logging
import platform
import psutil
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina import raycast
import time
from rubingMC.path_system import PathSystem
from rubingMC.terrain import TerrainGenerator

# 配置日志系统
log_path = os.path.join(os.getcwd(), 'MC.log')
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)
logging.info("=== 如冰制作我的世界DEMO启动中 ===")

# 新增系统信息日志
try:
    system_name = platform.system()
    
    # 更精确的Windows版本检测
    if system_name == "Windows":
        build_number = sys.getwindowsversion().build
        if build_number >= 22000:  # Windows 11起始构建号
            os_version = "Windows 11"
        else:
            os_version = f"Windows 10 (Build {build_number})"
    else:
        os_version = f"{system_name} {platform.release()}"

    mem = psutil.virtual_memory()
    logging.info(f"操作系统: {os_version}")
    logging.info(f"内存总量: {mem.total / (1024**3):.2f}GB")
    logging.info(f"可用内存: {mem.available / (1024**3):.2f}GB")
except Exception as e:
    logging.error(f"系统信息获取失败: {str(e)}")

# 获取用户输入
try:
    MAP_SIZE = int(input("请输入地形尺寸（32-256）: ") or 64)
    MAP_SIZE = max(32, min(256, MAP_SIZE))
except ValueError:
    logging.warning("输入无效，使用默认尺寸64")
    MAP_SIZE = 64

if __name__ == '__main__':
    app = Ursina(development_mode=False)  # 必须首先初始化Ursina应用
    window.title = f"分层地形生成 - {MAP_SIZE}x{MAP_SIZE}"
    window.size = (1600, 900)
    
    # 窗口设置（保持原样）
    window.position = (100, 100)
    window.borderless = False
    window.fps_counter.enabled = True
    window.cog_button.enabled = False
    window.vsync = True

    break_sound = None

    try:
        # 初始化玩家控制器
        player = FirstPersonController(position=(0, 50, 0))
        player.speed = 15
        player.gravity = 1.0

        # 生成地形
        generator = TerrainGenerator(MAP_SIZE)
        terrain = generator.build_terrain()
        terrain.y = -1
        
        # 环境设置
        sky_texture = load_texture('./assets/Sky/sky_default.jpg')
        Sky(texture=sky_texture)
        DirectionalLight(
            shadows=True,
            intensity=0.5,
            ambient=(0.8, 0.8, 0.8, 1)
        ).look_at(Vec3(1, -1, 0.5))

        last_break_time = 0  # 最后破坏时间戳
        break_cooldown = 0.1  # 冷却时间0.1秒

        # 新增改进的方块破坏功能
        def update():
            global last_break_time
            if held_keys['left mouse']:
                current_time = time.time()
                # 冷却时间检查
                if current_time - last_break_time < break_cooldown:
                    return

                # 射线检测逻辑
                hit_info = raycast(
                    origin=camera.world_position,
                    direction=camera.forward,
                    distance=10,
                    ignore=[player, terrain],
                    debug=False
                )
                
                if hit_info.hit and hasattr(hit_info.entity, 'is_block'):
                    # 执行破坏
                    destroy(hit_info.entity)
                    last_break_time = current_time  # 更新时间戳
                    
        app.run()
        logging.info("启动成功")
    except Exception as e:
        logging.critical(f"发生致命错误: {str(e)}", exc_info=True)
        input("按任意键退出...")