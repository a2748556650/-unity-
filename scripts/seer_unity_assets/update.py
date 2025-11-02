import asyncio
from datetime import datetime

import albi0
from pytz import timezone

from scripts._common import DataRepoManager, write_to_github_output
from scripts.seer_unity_assets.config import CONFIG

def get_manifest_path(package_name: str) -> str:
    return f"package-manifests/{package_name}.json"


def get_bundle_path(package_name: str) -> str:
    return f"newseer/assetbundles/{package_name}/*"


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


async def main():
    manager = DataRepoManager.from_checkout('.')
    for package_name, config in CONFIG.items():
        remote_version = await albi0.get_remote_version(config["updater_name"])
        print(f"⚙️ 正在更新资源包 {package_name}...")
        await process_package(
            package_name=package_name,
            updater_name=config["updater_name"],
            extractor_name=config["extractor_name"],
            update_args=config["update_args"],
        )
        print(f"✅ 资源包 {package_name} 更新完成")
        time_str = datetime.now(timezone("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%SUTC%z")
        manager.commit(f"{package_name}: Update to {remote_version} | Time: {time_str}")

    if manager.push():
        write_to_github_output("has_update", "true")


if __name__ == "__main__":
    asyncio.run(main())