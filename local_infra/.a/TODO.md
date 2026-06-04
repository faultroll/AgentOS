
1. 统一使用requirements.txt管理（即install, bootstrap, cleanup均从requirements.txt读取对应的包）
2. 尽量不要在特异化处理插件，而是按照固定模式循环处理（按照requirements.txt读取的结果，循环的进行 下载，安装，配置）
3. 插件增加sst-dev.opencode, gnassro.phi-agent, etienne-lescot.n8n-as-code；但只开启 luqimin.tiny-light, kilocode.kilo-code （Continue.continue以及新增插件默认保持关闭）
