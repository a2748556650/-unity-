import asyncio
from datetime import datetime

import albi0
import httpx
from pytz import timezone

from scripts._common import DataRepoManager, write_to_github_output

def get_manifest_path(package_name: str) -> str:
    return f"package-manifests/{package_name}.json"


def get_bundle_path(package_name: str) -> str:
    return f"newseer/assetbundles/{package_name}/*"


def check_current_version(package_name: str) -> str:
    res = httpx.get(f"https://raw.githubusercontent.com/SeerAPI/seer-unity-assets/refs/heads/main/{get_manifest_path(package_name)}")
    res.raise_for_status()
    return res.json()["version"]


async def process_package(
    *,
    package_name: str,
    updater_name: str,
    update_args: list[str],
    extractor_name: str,
):
    async with albi0.session():
        await albi0.update_resources(
            updater_name,
            *update_args,
            manifest_path=get_manifest_path(package_name),
        )
        await albi0.extract_assets(
            extractor_name,
            get_bundle_path(package_name),
            max_workers=2,
        )


CONFIG = {
    "ConfigPackage": {
        "updater_name": "newseer.config",
        "extractor_name": "newseer",
        "update_args": [],
    },
    "DefaultPackage": {
        "updater_name": "newseer.default",
        "extractor_name": "newseer",
        "update_args": [
            "*game_audios_cv*",
            "*art_ui_pettype*",
            "*art_ui_battleeffect*",
            "*art_ui_avatar*",
            "*art_ui_namecard*",
            "*assets_art_ui_assets_pet_head*",
            "*assets_art_ui_assets_pet_body*",
            "*assets_art_ui_assets_archive*",
            "*assets_art_ui_assets_countermark*",
            "*assets_art_ui_assets_item*",
        ],
    },
}


async def main():
    manager = DataRepoManager.from_checkout('.')
    for package_name, config in CONFIG.items():
        current_version = check_current_version(package_name)
        remote_version = await albi0.get_remote_version(config["updater_name"])
        if current_version == remote_version:
            print(f"📦 {package_name} 已是最新版本")
            continue

        print(f"🔄 {package_name} 需要更新，当前版本：{current_version}，远程版本：{remote_version}")
        print("⚙️  正在处理资源包...")
        await process_package(
            package_name=package_name,
            updater_name=config["updater_name"],
            extractor_name=config["extractor_name"],
            update_args=config["update_args"],
        )
        print("✅ 资源包处理完成")
        time_str = datetime.now(timezone("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%SUTC%z")
        manager.commit(f"{package_name}: Update to {remote_version} | Time: {time_str}")
    if manager.push():
        write_to_github_output("has_update", "true")


if __name__ == "__main__":
    asyncio.run(main())