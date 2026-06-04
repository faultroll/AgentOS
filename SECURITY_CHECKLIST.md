# Open Source Security Checklist

> 本检查清单用于在将代码公开发布前进行安全检查
> 基于 OpenSSF Security Baseline 和 CNCF Security Guidelines

## 检查项清单

### 1. 敏感信息泄露检查 (高优先级)

- [ ] **API Keys / Tokens**
  - 搜索: `api_key`, `apikey`, `token`, `secret`, `credential`
  - 检查常见格式: `sk-xxx`, `ghp_xxx`, `glpat-xxx`, `AKxxx`

- [ ] **密码和凭证**
  - 搜索: `password`, `passwd`, `pwd`
  - 检查数据库连接字符串

- [ ] **私钥**
  - 搜索: `private_key`, `privatekey`, `-----BEGIN`
  - 检查 `.pem`, `.key` 文件

- [ ] **邮箱地址**
  - 检查是否包含个人或内部邮箱

- [ ] **IP 地址**
  - 检查内网 IP (10.x.x.x, 192.168.x.x, 172.16-31.x.x)
  - 检查是否为硬编码的生产环境 IP

### 2. .gitignore 配置检查 (高优先级)

- [ ] **敏感文件排除**
  ```gitignore
  .env
  .env.local
  .env.production
  secrets/
  credentials/
  *.key
  *.pem
  ```

- [ ] **大型二进制文件排除**
  ```gitignore
  bin/
  models/
  *.gguf
  *.zip
  *.tar.gz
  ```

- [ ] **IDE/编辑器文件排除**
  ```gitignore
  .vscode/
  .idea/
  *.swp
  *.swo
  ```

### 3. 代码中的硬编码路径检查 (中优先级)

- [ ] **绝对路径**
  - Windows: `C:\`, `D:\`, `E:\`
  - Linux/macOS: `/home/`, `/Users/`
  - 网络路径: `\\server\`, `smb://`, `nfs://`

- [ ] **内部 URL**
  - 内网域名: `*.internal`, `*.local`, `*.corp`
  - 检查是否为硬编码的生产环境 URL

### 4. 日志和调试输出检查 (中优先级)

- [ ] **敏感信息打印**
  - 检查 `print()`, `console.log()`, `logger` 输出
  - 确保不打印: token、密码、个人信息

- [ ] **调试代码**
  - 检查是否遗留 `debugger`, `breakpoint`
  - 检查开发用的 `TODO`, `FIXME`, `HACK` 注释

### 5. 第三方依赖和下载链接检查 (中优先级)

- [ ] **依赖来源**
  - 确认所有依赖来自可信源 (官方仓库、GitHub 官方 release)
  - 检查是否有私有或内部仓库依赖

- [ ] **下载链接**
  - 确认 URL 使用 HTTPS
  - 检查链接是否指向可信域名

- [ ] **版本锁定**
  - 检查是否使用固定版本 (避免 `latest`)
  - 检查是否有 checksum/签名验证

### 6. 文档检查 (中优先级)

- [ ] **内部信息**
  - 检查是否包含内部服务器地址
  - 检查是否包含内部流程或工具

- [ ] **架构图**
  - 检查架构图是否暴露敏感信息

### 7. 脚本执行权限和安全风险 (低优先级)

- [ ] **脚本权限**
  - 检查脚本是否设置了合理的执行权限
  - 避免 `chmod 777`

- [ ] **命令注入风险**
  - 检查是否使用用户输入拼接命令
  - 检查 `eval()`, `exec()` 的使用

- [ ] **网络暴露**
  - 检查服务绑定地址 (`0.0.0.0` vs `127.0.0.1`)
  - 检查默认端口是否安全

## 自动化检查工具推荐

```bash
# 敏感信息扫描
gitleaks detect --source . --verbose
trivy filesystem --scanners secret .

# 依赖漏洞扫描
trivy filesystem --scanners vuln .
snyk test

# 静态代码分析
semgrep --config=auto .
bandit -r .  # Python
```

## 检查记录

| 日期 | 检查人 | 版本 | 结果 | 备注 |
|------|--------|------|------|------|
| 2026-06-04 | AI Assistant | local_infra | ✅ 通过 | 无敏感信息，适合公开发布 |

## 参考资源

- [OpenSSF Security Baseline](https://baseline.openssf.org/)
- [CNCF Security Hygiene Guide](https://contribute.cncf.io/projects/best-practices/security/security-hygiene/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
