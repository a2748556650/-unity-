import asyncio

import albi0
import httpx

from scripts._common import write_to_github_output
from scripts.seer_unity_assets.config import CONFIG
from scripts.seer_unity_assets.update import get_manifest_path


def get_current_version(package_name: str) -> str:
    res = httpx.get(f"https://raw.githubusercontent.com/SeerAPI/seer-unity-assets/refs/heads/main/{get_manifest_path(package_name)}")
    try:
        res.raise_for_status()
        return res.json()["version"]
    except httpx.HTTPStatusError:
        return "0.0.0"

def check_update(package_name: str) -> bool:
    current_version = get_current_version(package_name)
    remote_version = albi0.get_remote_version(package_name)
    return current_version != remote_version


async def run():
    albi0.load_all_plugins()

    need_update = False
    for package_name, config in CONFIG.items():
        current_version = get_current_version(package_name)
        remote_version = await albi0.get_remote_version(config["updater_name"])
        if current_version == remote_version:
            print(f"📦 {package_name} 已是最新版本")
            continue

        print(f"🔄 {package_name} 需要更新，当前版本：{current_version}，远程版本：{remote_version}")
        need_update = True

    write_to_github_output("need_update", "true" if need_update else "false")


def main():
    asyncio.run(run())
