# Copyright 2024 BeardedGiant
# https://github.com/bearded-giant/gitlab-tools
# Licensed under Apache License 2.0

"""Code search across GitLab group projects"""

import gitlab
import json
import os
import re
from datetime import datetime
from .base import BaseCommand


class CodeSearchCommand(BaseCommand):

    def handle(self, config, args, output_format):
        search_term = args.search_term
        group_path = args.group

        if args.extension:
            search_term = f"{search_term} extension:{args.extension}"

        gl = gitlab.Gitlab(config.gitlab_url, private_token=config.gitlab_token)

        try:
            group = gl.groups.get(group_path)
        except Exception as e:
            self.output_error(f"Group '{group_path}' not found: {e}", output_format)
            return

        # build project_id -> path_with_namespace map
        print(f"Loading projects for group '{group_path}'...")
        project_map = {}
        page = 1
        while True:
            projects = group.projects.list(
                per_page=100, page=page, include_subgroups=True
            )
            if not projects:
                break
            for p in projects:
                project_map[p.id] = p.path_with_namespace
            if len(projects) < 100:
                break
            page += 1
        print(f"Found {len(project_map)} projects")

        # paginate through all search results
        print(f"Searching for '{search_term}'...")
        all_results = []
        page = 1
        while True:
            try:
                results = group.search(
                    scope="blobs", search=search_term, per_page=100, page=page
                )
            except Exception as e:
                self.output_error(f"Search failed: {e}", output_format)
                return

            if not results:
                break
            all_results.extend(results)
            print(f"  fetched {len(all_results)} results...", end="\r")

            if len(results) < 100:
                break
            page += 1

        if not all_results:
            print(f"No results for '{args.search_term}' in group '{group_path}'")
            return

        # resolve project paths for results
        seen_projects = set()
        formatted = []
        for r in all_results:
            pid = r.get("project_id")
            project_path = project_map.get(pid)

            if not project_path:
                try:
                    proj = gl.projects.get(pid)
                    project_path = proj.path_with_namespace
                    project_map[pid] = project_path
                except Exception:
                    project_path = f"unknown-project-{pid}"

            seen_projects.add(project_path)
            startline = r.get("startline", "")
            file_path = r.get("path", r.get("filename", "unknown"))
            data = r.get("data", "").rstrip("\n")

            # truncate snippet: max 5 lines, max 200 chars per line
            data_lines = data.split("\n")[:5]
            data = "\n".join(
                line[:200] + "..." if len(line) > 200 else line
                for line in data_lines
            )

            formatted.append({
                "project": project_path,
                "path": file_path,
                "ref": r.get("ref", ""),
                "startline": startline,
                "data": data,
                "full_path": f"{project_path}/{file_path}",
            })

        if output_format == "json":
            output = {
                "results": formatted,
                "total": len(formatted),
                "projects_searched": len(seen_projects),
            }
            print(json.dumps(output, indent=2))
        else:
            lines = []
            for r in formatted:
                location = f"{r['full_path']}:{r['startline']}"
                snippet = r["data"]
                indented = "\n".join(
                    f"    {line}" for line in snippet.split("\n")
                )
                lines.append(f"{location}\n{indented}")

            output_text = "\n\n".join(lines)
            print(output_text)
            print(f"\nFound {len(formatted)} results across {len(seen_projects)} projects")

            # save to file
            cache_dir = args.out
            os.makedirs(cache_dir, exist_ok=True)

            slug = re.sub(r'[^a-z0-9]+', '-', args.search_term.lower())[:30].strip('-')
            stamp = datetime.now().strftime("%Y%m%d-%H%M")
            filename = f"search-{slug}-{stamp}.txt"
            out_path = os.path.join(cache_dir, filename)

            with open(out_path, "w") as f:
                f.write(output_text + "\n")

            # symlink latest
            link_path = os.path.join(cache_dir, "last_search.txt")
            if os.path.islink(link_path) or os.path.exists(link_path):
                os.remove(link_path)
            os.symlink(out_path, link_path)

            print(f"Results saved to {out_path}")
            print(f"Symlinked: last_search.txt -> {filename}")
