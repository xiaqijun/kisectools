# 项目名称
KisecTools

# 项目简介
KisecTools 是一个专注于任务管理和设备管理的工具，旨在为用户提供高效、便捷的管理体验。通过友好的用户界面和强大的功能，KisecTools 可以帮助用户轻松完成任务分配、设备选择等操作。

# 功能
- **任务管理**：
  - 创建任务：支持用户创建新的任务。
  - 查看任务：以列表形式展示所有任务，支持分页显示。
  - 删除任务：允许用户删除不需要的任务。
- **设备管理**：
  - 查询设备：支持用户查询设备信息。
  - 选择设备：用户可以选择特定设备进行操作。
- **分页显示**：
  - 支持分页查看任务列表，提升大数据量下的操作体验。

# 安装
1. 克隆项目：
   ```bash
   git clone <repository-url>
   ```
2. 进入项目目录：
   ```bash
   cd kisectools
   ```
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
4. 运行项目：
   ```bash
   python main.py
   ```

# 使用
1. 启动项目后，打开浏览器，访问 `http://localhost:8000`。
2. 在任务管理页面，用户可以创建、查看和删除任务。
3. 在设备管理页面，用户可以查询和选择设备。

# 目录结构
```
main.py                # 项目入口文件
README.md              # 项目描述文件
requirements.txt       # 项目依赖文件
kisectools/            # 核心功能模块
    __init__.py        # 包初始化文件
    config_temp.py     # 配置模板文件
    config.py          # 配置文件
    device.py          # 设备管理模块
    models.py          # 数据模型模块
    plugin.py          # 插件管理模块
    task.py            # 任务管理模块
    templates/         # 前端模板文件
        base.html      # 基础模板
        device.html    # 设备管理页面模板
        login.html     # 登录页面模板
        plugin.html    # 插件管理页面模板
        task.html      # 任务管理页面模板
migrations/            # 数据库迁移文件
    alembic.ini        # Alembic 配置文件
    env.py             # 数据库环境配置
    README             # 迁移工具说明
    script.py.mako     # 迁移脚本模板
    versions/          # 数据库版本文件夹
        b05b78ff94ae_.py  # 数据库版本迁移脚本
```

# 贡献
我们欢迎所有形式的贡献！
- 提交问题：如果您在使用过程中遇到问题，请通过 Issue 提交。
- 提交代码：欢迎通过 Pull Request 提交改进代码。

# 许可证
本项目基于 MIT 许可证开源，详情请参阅 LICENSE 文件。