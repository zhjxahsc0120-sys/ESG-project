# 本地 MySQL 实例连接说明

当前 MySQL 使用免安装 zip 方式部署在 E 盘，不注册 Windows 服务。

## 安装位置

```text
MySQL Home: E:\mysql\mysql-8.4.9-winx64
Data Dir:   E:\mysql\data-8.4-luoyi
Config:     E:\mysql\my-luoyi.cnf
SQL Copy:   E:\mysql\luoyi-sql
```

## 连接信息

```text
Host: 127.0.0.1
Port: 3307
Database: luoyi_esg
Root user: root
Root password: Luoyi_Root_2026!
App user: luoyi_app
App password: Luoyi_App_2026!
```

## 启动

```powershell
Start-Process -FilePath "E:\mysql\mysql-8.4.9-winx64\bin\mysqld.exe" -ArgumentList "--defaults-file=E:\mysql\my-luoyi.cnf" -WindowStyle Hidden
```

## 停止

```powershell
E:\mysql\mysql-8.4.9-winx64\bin\mysqladmin.exe --host=127.0.0.1 --port=3307 --user=root --password=Luoyi_Root_2026! shutdown
```

## 执行校验

```powershell
E:\mysql\mysql-8.4.9-winx64\bin\mysql.exe --host=127.0.0.1 --port=3307 --user=root --password=Luoyi_Root_2026! --default-character-set=utf8mb4 luoyi_esg < E:\mysql\luoyi-sql\06_validation_queries.sql
```

## 说明

当前实例用于罗宜高速 ESG 原型后端联调和数据库设计验证。未注册系统服务，重启电脑后需要手动启动。
