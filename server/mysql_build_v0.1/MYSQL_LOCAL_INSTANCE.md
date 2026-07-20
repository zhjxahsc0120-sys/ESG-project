# 本地 MySQL 实例连接说明

当前 MySQL 使用免安装 zip 方式部署，不注册 Windows 服务。

## 默认连接参数

```text
Host: 127.0.0.1
Port: 3307
Database: luoyi_esg
App user: luoyi_app
Password: 通过 LUOYI_MYSQL_PASSWORD 环境变量设置
```

完整环境变量见项目根目录 `.env.example`。真实口令只能保存在本地 `.env`、服务器环境变量或密钥管理系统中，不得提交到仓库。

## 启动与验证

启动 MySQL 后，设置当前终端所需的环境变量，再启动后端：

```powershell
$env:LUOYI_DB_MODE = "mysql"
$env:LUOYI_MYSQL_HOST = "127.0.0.1"
$env:LUOYI_MYSQL_PORT = "3307"
$env:LUOYI_MYSQL_DATABASE = "luoyi_esg"
$env:LUOYI_MYSQL_USER = "luoyi_app"
$env:LUOYI_MYSQL_PASSWORD = Read-Host "MySQL password"
powershell.exe -ExecutionPolicy Bypass -File .\server\start_backend.ps1
```

当前实例仅用于罗宜高速 ESG 原型后端联调和数据库设计验证。
