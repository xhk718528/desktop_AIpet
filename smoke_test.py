"""无 GUI 冒烟测试：验证 agno Agent 能调用系统工具与 FileTools。"""
from pcpet.agent_core import create_agent
from pcpet import config

config.ensure_dirs()
agent = create_agent()

def ask(q):
    print("\n" + "=" * 60)
    print("Q:", q)
    print("-" * 60)
    r = agent.run(q)
    print("A:", r.content)

print(">>> 已创建 Agent，开始冒烟测试...")

ask("帮我做个电脑体检，说说CPU和内存情况")
ask("请你把一句话写进文件 hi.txt（在我的文件目录里），然后读出来给我看")
ask("现在 files 目录里有哪些文件（列出文件名即可）")

print("\n>>> 冒烟测试完成 ✅")
