"""
Pico部署工具
智能部署代码和依赖到Pico设备，支持增量更新
"""
import os
import sys
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
        # 重新配置stdout以使用utf-8
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


class PicoDeployer:
    """Pico部署器"""
    
    # Pico设备可能的挂载点
    POSSIBLE_MOUNT_POINTS = [
        "E:",      # Windows常见盘符
        "F:",
        "G:",
        "H:",
        "D:",
        "/media/CIRCUITPY",  # Linux
        "/Volumes/CIRCUITPY",  # macOS
    ]
    
    # 部署记录文件（存储在Pico上）
    DEPLOY_RECORD_FILE = ".deploy_record.json"
    
    def __init__(self, project_root=None):
        """
        初始化部署器
        
        Args:
            project_root: 项目根目录，默认为脚本所在目录的上级目录
        """
        if project_root is None:
            project_root = Path(__file__).parent.parent
        
        self.project_root = Path(project_root)
        self.app_dir = self.project_root / "app"
        self.lib_dir = self.project_root / "lib"
        self.pico_path = None
        self.deploy_record = {}
        
        print(f"项目根目录: {self.project_root}")
        print(f"应用目录: {self.app_dir}")
        print(f"库目录: {self.lib_dir}")
    
    def find_pico(self):
        """查找Pico设备"""
        print("\n正在查找Pico设备...")
        
        for mount_point in self.POSSIBLE_MOUNT_POINTS:
            mount_path = Path(mount_point)
            if mount_path.exists():
                # 检查是否为CircuitPython设备
                boot_out = mount_path / "boot_out.txt"
                if boot_out.exists():
                    with open(boot_out, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if 'Adafruit CircuitPython' in content or 'CircuitPython' in content:
                            self.pico_path = mount_path
                            print(f"✓ 找到Pico设备: {mount_path}")
                            return True
        
        print("✗ 未找到Pico设备")
        print("\n请确保:")
        print("  1. Pico已连接到电脑")
        print("  2. Pico已安装CircuitPython固件")
        print("  3. Pico显示为CIRCUITPY盘符")
        return False
    
    def load_deploy_record(self):
        """加载部署记录"""
        if self.pico_path is None:
            return
        
        record_file = self.pico_path / self.DEPLOY_RECORD_FILE
        if record_file.exists():
            try:
                with open(record_file, 'r', encoding='utf-8') as f:
                    self.deploy_record = json.load(f)
                print(f"✓ 加载部署记录: {len(self.deploy_record)} 个文件")
            except Exception as e:
                print(f"⚠ 加载部署记录失败: {e}")
                self.deploy_record = {}
        else:
            print("○ 首次部署，未找到部署记录")
            self.deploy_record = {}
    
    def save_deploy_record(self):
        """保存部署记录"""
        if self.pico_path is None:
            return
        
        record_file = self.pico_path / self.DEPLOY_RECORD_FILE
        try:
            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(self.deploy_record, f, indent=2)
            print(f"✓ 保存部署记录: {len(self.deploy_record)} 个文件")
        except Exception as e:
            print(f"⚠ 保存部署记录失败: {e}")
    
    def calculate_file_hash(self, file_path):
        """
        计算文件的MD5哈希值
        
        Args:
            file_path: 文件路径
        
        Returns:
            str: MD5哈希值
        """
        md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception as e:
            print(f"⚠ 计算文件哈希失败 {file_path}: {e}")
            return None
    
    def should_copy_file(self, src_path, dest_path, relative_path):
        """
        判断是否需要复制文件
        
        Args:
            src_path: 源文件路径
            dest_path: 目标文件路径
            relative_path: 相对路径（用于记录）
        
        Returns:
            bool: 是否需要复制
        """
        # 如果目标文件不存在，必须复制
        if not dest_path.exists():
            return True
        
        # 计算源文件哈希
        src_hash = self.calculate_file_hash(src_path)
        if src_hash is None:
            return True
        
        # 检查记录中的哈希
        record_key = str(relative_path).replace('\\', '/')
        if record_key in self.deploy_record:
            recorded_hash = self.deploy_record[record_key].get('hash')
            if recorded_hash == src_hash:
                # 哈希匹配，无需复制
                return False
        
        return True
    
    def copy_file(self, src_path, dest_path, relative_path):
        """
        复制文件并更新记录
        
        Args:
            src_path: 源文件路径
            dest_path: 目标文件路径
            relative_path: 相对路径（用于记录）
        
        Returns:
            bool: 是否成功
        """
        try:
            # 创建目标目录
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            shutil.copy2(src_path, dest_path)
            
            # 计算哈希并更新记录
            file_hash = self.calculate_file_hash(src_path)
            record_key = str(relative_path).replace('\\', '/')
            self.deploy_record[record_key] = {
                'hash': file_hash,
                'size': src_path.stat().st_size,
                'mtime': datetime.now().isoformat(),
            }
            
            return True
        except Exception as e:
            print(f"✗ 复制文件失败 {src_path} -> {dest_path}: {e}")
            return False
    
    def deploy_app(self):
        """部署应用代码"""
        print("\n" + "="*60)
        print("部署应用代码")
        print("="*60)
        
        if not self.app_dir.exists():
            print(f"✗ 应用目录不存在: {self.app_dir}")
            return False
        
        # 获取所有应用文件
        app_files = []
        for root, dirs, files in os.walk(self.app_dir):
            # 跳过__pycache__等目录
            dirs[:] = [d for d in dirs if not d.startswith('__') and d != '.git']
            
            for file in files:
                if file.startswith('.') or file.endswith('.pyc'):
                    continue
                
                src_path = Path(root) / file
                rel_path = src_path.relative_to(self.app_dir)
                app_files.append((src_path, rel_path))
        
        print(f"找到 {len(app_files)} 个应用文件")
        
        # 复制文件
        copied = 0
        skipped = 0
        failed = 0
        
        for src_path, rel_path in app_files:
            dest_path = self.pico_path / rel_path
            
            # 检查是否需要复制
            if self.should_copy_file(src_path, dest_path, rel_path):
                if self.copy_file(src_path, dest_path, rel_path):
                    print(f"  ✓ {rel_path}")
                    copied += 1
                else:
                    failed += 1
            else:
                print(f"  ○ {rel_path} (跳过，未改变)")
                skipped += 1
        
        print(f"\n应用代码部署完成:")
        print(f"  复制: {copied} 个")
        print(f"  跳过: {skipped} 个")
        if failed > 0:
            print(f"  失败: {failed} 个")
        
        return failed == 0
    
    def deploy_lib(self):
        """部署依赖库"""
        print("\n" + "="*60)
        print("部署依赖库")
        print("="*60)
        
        if not self.lib_dir.exists():
            print(f"✗ 库目录不存在: {self.lib_dir}")
            return False
        
        # 创建Pico上的lib目录
        pico_lib_dir = self.pico_path / "lib"
        pico_lib_dir.mkdir(exist_ok=True)
        
        # 获取所有库文件
        lib_files = []
        for root, dirs, files in os.walk(self.lib_dir):
            # 跳过__pycache__等目录
            dirs[:] = [d for d in dirs if not d.startswith('__') and d != '.git']
            
            for file in files:
                if file.startswith('.') or file.endswith('.pyc'):
                    continue
                
                src_path = Path(root) / file
                rel_path = src_path.relative_to(self.lib_dir)
                lib_files.append((src_path, rel_path))
        
        print(f"找到 {len(lib_files)} 个库文件")
        
        # 复制文件
        copied = 0
        skipped = 0
        failed = 0
        
        for src_path, rel_path in lib_files:
            dest_path = pico_lib_dir / rel_path
            full_rel_path = Path("lib") / rel_path
            
            # 检查是否需要复制
            if self.should_copy_file(src_path, dest_path, full_rel_path):
                if self.copy_file(src_path, dest_path, full_rel_path):
                    print(f"  ✓ lib/{rel_path}")
                    copied += 1
                else:
                    failed += 1
            else:
                print(f"  ○ lib/{rel_path} (跳过，未改变)")
                skipped += 1
        
        print(f"\n依赖库部署完成:")
        print(f"  复制: {copied} 个")
        print(f"  跳过: {skipped} 个")
        if failed > 0:
            print(f"  失败: {failed} 个")
        
        return failed == 0
    
    def clean_old_files(self, dry_run=False):
        """
        清理Pico上不在项目中的旧文件
        
        Args:
            dry_run: 如果为True，只显示将要删除的文件，不实际删除
        """
        print("\n" + "="*60)
        print("检查旧文件" if dry_run else "清理旧文件")
        print("="*60)
        
        # 获取项目中的所有文件（相对路径）
        project_files = set()
        
        # 应用文件
        if self.app_dir.exists():
            for root, dirs, files in os.walk(self.app_dir):
                dirs[:] = [d for d in dirs if not d.startswith('__') and d != '.git']
                for file in files:
                    if file.startswith('.') or file.endswith('.pyc'):
                        continue
                    src_path = Path(root) / file
                    rel_path = src_path.relative_to(self.app_dir)
                    project_files.add(str(rel_path).replace('\\', '/'))
        
        # 库文件
        if self.lib_dir.exists():
            for root, dirs, files in os.walk(self.lib_dir):
                dirs[:] = [d for d in dirs if not d.startswith('__') and d != '.git']
                for file in files:
                    if file.startswith('.') or file.endswith('.pyc'):
                        continue
                    src_path = Path(root) / file
                    rel_path = src_path.relative_to(self.lib_dir)
                    project_files.add(f"lib/{str(rel_path).replace(chr(92), '/')}")
        
        # 检查Pico上的文件
        to_delete = []
        for record_key in list(self.deploy_record.keys()):
            if record_key not in project_files:
                to_delete.append(record_key)
        
        if not to_delete:
            print("○ 没有需要清理的旧文件")
            return True
        
        print(f"发现 {len(to_delete)} 个旧文件:")
        for file_path in to_delete:
            print(f"  - {file_path}")
        
        if dry_run:
            print("\n提示: 使用 --clean 参数执行实际清理")
            return True
        
        # 执行删除
        deleted = 0
        failed = 0
        for file_path in to_delete:
            pico_file = self.pico_path / file_path
            try:
                if pico_file.exists():
                    pico_file.unlink()
                    print(f"  ✓ 删除 {file_path}")
                del self.deploy_record[file_path]
                deleted += 1
            except Exception as e:
                print(f"  ✗ 删除失败 {file_path}: {e}")
                failed += 1
        
        print(f"\n清理完成:")
        print(f"  删除: {deleted} 个")
        if failed > 0:
            print(f"  失败: {failed} 个")
        
        return failed == 0
    
    def show_status(self):
        """显示部署状态"""
        print("\n" + "="*60)
        print("部署状态")
        print("="*60)
        
        if not self.deploy_record:
            print("○ 尚未部署任何文件")
            return
        
        # 统计
        app_files = []
        lib_files = []
        total_size = 0
        
        for file_path, info in self.deploy_record.items():
            size = info.get('size', 0)
            total_size += size
            
            if file_path.startswith('lib/'):
                lib_files.append((file_path, size))
            else:
                app_files.append((file_path, size))
        
        print(f"\n应用文件: {len(app_files)} 个")
        for file_path, size in sorted(app_files):
            print(f"  {file_path:40s} {size:>8d} 字节")
        
        print(f"\n依赖库: {len(lib_files)} 个")
        for file_path, size in sorted(lib_files):
            print(f"  {file_path:40s} {size:>8d} 字节")
        
        print(f"\n总计: {len(self.deploy_record)} 个文件, {total_size:,} 字节 ({total_size/1024:.1f} KB)")
        
        # 最后部署时间
        if self.deploy_record:
            latest_mtime = max(info.get('mtime', '') for info in self.deploy_record.values())
            if latest_mtime:
                print(f"最后部署: {latest_mtime}")
    
    def deploy(self, clean=False, force=False):
        """
        执行完整部署
        
        Args:
            clean: 是否清理旧文件
            force: 是否强制重新部署所有文件
        
        Returns:
            bool: 是否成功
        """
        print("\n" + "="*60)
        print("Pico2W 部署工具")
        print("="*60)
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 查找Pico设备
        if not self.find_pico():
            return False
        
        # 加载部署记录
        if not force:
            self.load_deploy_record()
        else:
            print("○ 强制部署模式，忽略部署记录")
            self.deploy_record = {}
        
        # 部署应用代码
        if not self.deploy_app():
            print("\n✗ 应用代码部署失败")
            return False
        
        # 部署依赖库
        if not self.deploy_lib():
            print("\n✗ 依赖库部署失败")
            return False
        
        # 清理旧文件
        if clean:
            self.clean_old_files(dry_run=False)
        
        # 保存部署记录
        self.save_deploy_record()
        
        # 显示状态
        self.show_status()
        
        print("\n" + "="*60)
        print("✓ 部署完成！")
        print("="*60)
        print("\n提示:")
        print("  - 按 Ctrl+D 重启Pico设备")
        print("  - 使用串口监控工具查看输出")
        
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Pico2W 部署工具 - 智能部署代码和依赖',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python deploy.py                 # 增量部署
  python deploy.py --clean         # 部署并清理旧文件
  python deploy.py --force         # 强制重新部署所有文件
  python deploy.py --status        # 查看部署状态
  python deploy.py --check-clean   # 检查需要清理的文件（不实际删除）
        """
    )
    
    parser.add_argument('--clean', action='store_true',
                        help='清理Pico上不在项目中的旧文件')
    parser.add_argument('--force', action='store_true',
                        help='强制重新部署所有文件（忽略哈希检查）')
    parser.add_argument('--status', action='store_true',
                        help='仅显示部署状态，不执行部署')
    parser.add_argument('--check-clean', action='store_true',
                        help='检查需要清理的文件（不实际删除）')
    parser.add_argument('--project-root', type=str,
                        help='项目根目录（默认为脚本所在目录的上级目录）')
    
    args = parser.parse_args()
    
    # 创建部署器
    deployer = PicoDeployer(project_root=args.project_root)
    
    # 查找Pico
    if not deployer.find_pico():
        sys.exit(1)
    
    # 加载记录
    deployer.load_deploy_record()
    
    # 根据参数执行操作
    if args.status:
        deployer.show_status()
    elif args.check_clean:
        deployer.clean_old_files(dry_run=True)
    else:
        success = deployer.deploy(clean=args.clean, force=args.force)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
