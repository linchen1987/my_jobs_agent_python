## Tips
- agent 不需要自动操作 .env file. 只需参考 .env.example.
- 注意添加错误日志，方便后续排查调试问题
- 编写函数或模块时要注意兼顾易用性和灵活性
- 所有脚本需要从根引用模块，例如 `from jobs_agent.xxx.xxx` (本项目顶级包名为 `jobs_agent`)

## Overview
- This is a python project, use uv