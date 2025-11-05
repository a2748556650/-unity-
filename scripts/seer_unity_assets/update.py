import asyncio

import albi0

from scripts._common import DataRepoManager, get_current_time_str, write_to_github_output
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


async def run():
    albi0.load_all_plugins()

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
        manager.commit_and_push(
            f"{package_name}: Update to {remote_version} | Time: {get_current_time_str()}",
            files=["package-manifests/", f"{config['extractor_name']}/assets/"]
        )

    if manager.push():
        write_to_github_output("has_update", "true")


def main():
    asyncio.run(run())