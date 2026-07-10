from ..base_module import BaseModule
from typing import Any, Dict, List
import subprocess
import logging

logger = logging.getLogger(__name__)


class GitHubModule(BaseModule):
    def __init__(self):
        super().__init__(
            name="github",
            description="Gerenciar repos, issues, PRs e workflows via GitHub CLI (gh)"
        )
        self._gh_available = False

    def _load_resources(self):
        logger.info("Carregando recursos do GitHub...")

        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            self._gh_available = result.returncode == 0
        except FileNotFoundError:
            self._gh_available = False

        self._metadata = {
            "version": "1.0",
            "gh_available": self._gh_available,
            "capabilities": [
                "list_repos",
                "list_issues",
                "create_issue",
                "list_prs",
                "create_pr",
                "view_repo"
            ]
        }

    def _unload_resources(self):
        self._gh_available = False
        logger.info("Recursos do GitHub liberados")

    def execute(self, action: str, **kwargs) -> Any:
        if not self._gh_available:
            raise RuntimeError("GitHub CLI (gh) não está disponível")

        actions = {
            "repos": self._list_repos,
            "issues": self._list_issues,
            "create_issue": self._create_issue,
            "prs": self._list_prs,
            "repo": self._view_repo
        }

        if action not in actions:
            raise ValueError(f"Ação não suportada: {action}")

        return actions[action](**kwargs)

    def _run_gh(self, args: List[str]) -> str:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            raise RuntimeError(f"Erro gh: {result.stderr}")
        return result.stdout

    def _list_repos(self, **kwargs) -> List[Dict]:
        output = self._run_gh(["repo", "list", "--limit", "10", "--json",
                               "name,description,url,isPrivate"])
        import json
        return json.loads(output)

    def _list_issues(self, repo: str = None, **kwargs) -> List[Dict]:
        args = ["issue", "list", "--limit", "10", "--json",
                "number,title,state,author"]
        if repo:
            args.extend(["--repo", repo])
        output = self._run_gh(args)
        import json
        return json.loads(output)

    def _create_issue(self, repo: str, title: str, body: str = "", **kwargs) -> Dict:
        output = self._run_gh(["issue", "create", "--repo", repo,
                               "--title", title, "--body", body])
        return {"url": output.strip()}

    def _list_prs(self, repo: str = None, **kwargs) -> List[Dict]:
        args = ["pr", "list", "--limit", "10", "--json",
                "number,title,state,author"]
        if repo:
            args.extend(["--repo", repo])
        output = self._run_gh(args)
        import json
        return json.loads(output)

    def _view_repo(self, repo: str, **kwargs) -> Dict:
        output = self._run_gh(["repo", "view", repo, "--json",
                               "name,description,url,defaultBranchRef"])
        import json
        return json.loads(output)
