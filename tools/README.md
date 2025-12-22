# 开发工具

本目录包含用于Pico2W开发的实用工具。

## 部署工具 (deploy.py)

智能部署工具，支持增量更新和依赖管理。

### 功能特性

- ✅ **自动查找Pico设备** - 支持Windows/Linux/macOS
- ✅ **增量部署** - 只复制变化的文件，节省时间
- ✅ **哈希校验** - 使用MD5检测文件变化
- ✅ **依赖管理** - 记录已部署的库文件，避免重复写入
- ✅ **旧文件清理** - 可选清理Pico上不在项目中的文件
- ✅ **部署记录** - 在Pico上保存部署历史
- ✅ **详细日志** - 显示每个文件的部署状态

### 使用方法

#### 基本部署（增量）
```bash
# Python方式
python tools/deploy.py

# Windows快捷方式
tools\deploy.bat

# Linux/macOS快捷方式
./tools/deploy.sh
```

#### 查看部署状态
```bash
python tools/deploy.py --status
```

#### 清理旧文件
```bash
# 检查需要清理的文件（不实际删除）
python tools/deploy.py --check-clean

# 部署并清理旧文件
python tools/deploy.py --clean
```

#### 强制重新部署
```bash
# 忽略哈希检查，重新部署所有文件
python tools/deploy.py --force
```

#### 完整选项
```bash
python tools/deploy.py [选项]

选项:
  --clean           清理Pico上不在项目中的旧文件
  --force           强制重新部署所有文件（忽略哈希检查）
  --status          仅显示部署状态，不执行部署
  --check-clean     检查需要清理的文件（不实际删除）
  --project-root    指定项目根目录
  -h, --help        显示帮助信息
```

### 部署流程

1. **查找Pico设备**
   - 自动扫描可能的挂载点
   - 验证是否为CircuitPython设备

2. **加载部署记录**
   - 读取Pico上的 `.deploy_record.json`
   - 包含文件哈希、大小、时间等信息

3. **部署应用代码**
   - 扫描 `app/` 目录下的所有文件
   - 计算文件哈希，与记录对比
   - 只复制变化的文件

4. **部署依赖库**
   - 扫描 `lib/` 目录下的所有文件
   - 同样使用哈希检测变化
   - 复制到Pico的 `lib/` 目录

5. **清理旧文件**（可选）
   - 删除Pico上不在项目中的文件
   - 释放存储空间

6. **保存部署记录**
   - 更新 `.deploy_record.json`
   - 记录所有已部署文件的信息

### 部署记录格式

`.deploy_record.json` 存储在Pico根目录：

```json
{
  "code.py": {
    "hash": "abc123...",
    "size": 1234,
    "mtime": "2025-12-23T10:30:00"
  },
  "lib/adafruit_pca9685.mpy": {
    "hash": "def456...",
    "size": 5678,
    "mtime": "2025-12-23T10:30:00"
  }
}
```

### 输出示例

```
==================================================
Pico2W 部署工具
==================================================
时间: 2025-12-23 10:30:00

正在查找Pico设备...
✓ 找到Pico设备: E:
✓ 加载部署记录: 8 个文件

==================================================
部署应用代码
==================================================
找到 5 个应用文件
  ✓ code.py
  ○ servo_controller.py (跳过，未改变)
  ○ web_server.py (跳过，未改变)
  ✓ config.json
  ○ code_with_config.py (跳过，未改变)

应用代码部署完成:
  复制: 2 个
  跳过: 3 个

==================================================
部署依赖库
==================================================
找到 12 个库文件
  ○ lib/adafruit_pca9685.mpy (跳过，未改变)
  ○ lib/adafruit_motor/__init__.mpy (跳过，未改变)
  ...

依赖库部署完成:
  复制: 0 个
  跳过: 12 个

✓ 保存部署记录: 17 个文件

==================================================
部署状态
==================================================

应用文件: 5 个
  code.py                                     3456 字节
  config.json                                  789 字节
  ...

依赖库: 12 个
  lib/adafruit_pca9685.mpy                   12345 字节
  ...

总计: 17 个文件, 45,678 字节 (44.6 KB)
最后部署: 2025-12-23T10:30:00

==================================================
✓ 部署完成！
==================================================

提示:
  - 按 Ctrl+D 重启Pico设备
  - 使用串口监控工具查看输出
```

### 工作原理

#### 哈希检测
使用MD5哈希检测文件变化：
- 计算本地文件的MD5
- 与部署记录中的哈希比对
- 只有哈希不同时才复制文件

#### 增量部署优势
- ⚡ **速度快** - 跳过未改变的文件
- 💾 **减少写入** - 延长闪存寿命
- 🔍 **精确追踪** - 知道哪些文件已部署

#### 文件过滤
自动跳过：
- 隐藏文件（以 `.` 开头）
- Python字节码（`.pyc`）
- `__pycache__` 目录
- `.git` 目录

### 故障排除

#### 找不到Pico设备
- 确保Pico已连接到电脑
- 确认已安装CircuitPython固件
- 检查是否显示为CIRCUITPY盘符
- Windows: 检查设备管理器
- Linux: 检查 `/media/` 目录
- macOS: 检查 `/Volumes/` 目录

#### 权限错误
- Windows: 以管理员身份运行
- Linux/macOS: 使用 `sudo` 或修改设备权限

#### 文件被占用
- 关闭其他访问Pico的程序
- 断开串口监控连接
- 重新连接Pico

#### 部署后代码不运行
- 按 Ctrl+D 重启Pico
- 检查串口输出查看错误
- 确认所有依赖库都已部署

### 与其他工具集成

#### VS Code任务
在 `.vscode/tasks.json` 中添加：

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Deploy to Pico",
      "type": "shell",
      "command": "python",
      "args": ["tools/deploy.py"],
      "group": {
        "kind": "build",
        "isDefault": true
      }
    }
  ]
}
```

#### 快捷键
在 `.vscode/keybindings.json` 中添加：

```json
[
  {
    "key": "ctrl+shift+d",
    "command": "workbench.action.tasks.runTask",
    "args": "Deploy to Pico"
  }
]
```

### 高级用法

#### 自定义挂载点
```python
deployer = PicoDeployer()
deployer.POSSIBLE_MOUNT_POINTS.append("Z:")
```

#### 编程方式使用
```python
from tools.deploy import PicoDeployer

deployer = PicoDeployer()
if deployer.find_pico():
    deployer.load_deploy_record()
    deployer.deploy(clean=True, force=False)
```

## 其他工具

### monitor.py（计划中）
串口监控工具，实时查看Pico输出。

### watcher.py（计划中）
文件监控工具，自动检测变化并部署。

## 贡献

欢迎提交改进建议和Pull Request！
