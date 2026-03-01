import subprocess
import sys
from typing import Any

from hatchling.builders.config import BuilderConfigBound
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class BuildHook(BuildHookInterface[BuilderConfigBound]):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        subprocess.check_call([sys.executable, "-m", "ziglang", "build", "--release=safe"])
