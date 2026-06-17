# Wiki 源文件

本目录是 **GitHub Wiki 的源文件**。Wiki 在浏览器里编辑很爽，但内容不进 git、不能 review、不能 diff —— 对工程化项目不友好。

## 工作流

Wiki 源文件随主仓库 git 管理，**主仓库一次提交包含代码 + 文档改动**。
推到 Wiki 用 `git push`，从主仓库目录直接操作：

```bash
# 首次：克隆 Wiki 仓库作为 worktree（避免污染主仓库）
git clone https://github.com/Joy-Forge/df_ai_tools.wiki.git ../df_ai_tools.wiki

# 推送（手动）
cp docs/wiki/*.md ../df_ai_tools.wiki/
cd ../df_ai_tools.wiki
git add . && git commit -m "docs: sync wiki" && git push origin master
```

> 替代方案：用 git worktree 把 Wiki 挂到主仓库的 `docs/wiki-wt/` 目录，避免 copy。

### 协作约定

- **不要**在 GitHub 网页上直接改 Wiki —— 改完下次同步会被覆盖
- 模块文档的字段表必须与 `src/<module>/tools.py` 中的签名一致；改代码时**同时**改 `docs/wiki/<Module>.md`
- 长期内容进 Wiki；项目门面（5 分钟跑起来）保持在 `README.md`
