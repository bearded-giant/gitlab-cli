# Copyright 2024 BeardedGiant
# https://github.com/bearded-giant/gitlab-tools
# Licensed under Apache License 2.0

"""Base command class with common functionality"""

import sys
import json
from typing import List


class BaseCommand:
    """Base class for all command handlers"""

    def parse_ids(self, id_string: str) -> List[int]:
        ids = []
        for part in id_string.split(","):
            try:
                ids.append(int(part.strip()))
            except ValueError:
                print(f"Invalid ID: {part}")
                sys.exit(1)
        return ids

    def output_json(self, data):
        print(json.dumps(data, indent=2))

    def output_error(self, message: str, output_format: str = "friendly"):
        if output_format == "json":
            self.output_json({"error": message, "status": "error"})
        else:
            print(f"❌ Error: {message}", file=sys.stderr)
        sys.exit(1)

    def format_duration(self, duration):
        if duration is None:
            return "N/A"

        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)

        if hours > 0:
            return f"{hours}h{minutes}m{seconds}s"
        elif minutes > 0:
            return f"{minutes}m{seconds}s"
        else:
            return f"{seconds}s"

