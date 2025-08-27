-- MySQL初始化脚本
-- 设置字符集和排序规则

-- 创建qtrade数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS `qtrade` 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

-- 使用qtrade数据库
USE `qtrade`;

-- 设置时区
SET time_zone = '+08:00';

-- 创建用户（如果不存在）
CREATE USER IF NOT EXISTS 'qtrade'@'%' IDENTIFIED BY 'qtrade123';

-- 授权
GRANT ALL PRIVILEGES ON `qtrade`.* TO 'qtrade'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, CREATE TEMPORARY TABLES, LOCK TABLES ON `qtrade`.* TO 'qtrade'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 显示创建结果
SELECT 'MySQL初始化完成' AS message;
SHOW DATABASES;
SELECT User, Host FROM mysql.user WHERE User = 'qtrade';