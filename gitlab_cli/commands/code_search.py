# Copyright 2024 BeardedGiant
# https://github.com/bearded-giant/gitlab-tools
# Licensed under Apache License 2.0

"""Code search across GitLab group projects"""

import csv
import gitlab
import io
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

        include_comments = getattr(args, "comments", False)

        # resolve project paths and filter excludes
        excludes = getattr(args, "exclude", []) or []
        seen_projects = set()
        last_seen_line = {}
        excluded_count = 0
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

            if any(ex in project_path for ex in excludes):
                excluded_count += 1
                continue

            if not include_comments:
                snippet_raw = r.get("data", "")
                lines = snippet_raw.split("\n")

                # check if snippet is inside a docstring:
                # any line contains a triple-quote delimiter
                has_docstring = any(
                    '"""' in sl or "'''" in sl for sl in lines
                )
                if has_docstring:
                    excluded_count += 1
                    continue

                # check first non-empty line for comment patterns
                first_line = ""
                for sl in lines:
                    stripped = sl.strip()
                    if stripped:
                        first_line = stripped
                        break
                if first_line.startswith(("#", "//", "/*", "*", "--", "<!--")):
                    excluded_count += 1
                    continue

            # deduplicate: skip results within 3 lines of a previous hit in same file
            startline = r.get("startline", 0)
            file_path = r.get("path", r.get("filename", "unknown"))
            full_key = f"{project_path}/{file_path}"
            try:
                startline_int = int(startline)
            except (ValueError, TypeError):
                startline_int = 0

            if full_key in last_seen_line and startline_int - last_seen_line[full_key] <= 3:
                excluded_count += 1
                continue
            last_seen_line[full_key] = startline_int

            seen_projects.add(project_path)
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

        files_only = getattr(args, "files_only", False)

        if output_format == "json":
            if files_only:
                unique_files = sorted(set(r["full_path"] for r in formatted))
                output = {"files": unique_files, "total": len(unique_files)}
            else:
                output = {
                    "results": formatted,
                    "total": len(formatted),
                    "projects_searched": len(seen_projects),
                }
            print(json.dumps(output, indent=2))
            return

        excluded_msg = f" ({excluded_count} excluded)" if excluded_count else ""

        if files_only:
            unique_files = sorted(set(r["full_path"] for r in formatted))
            output_text = "\n".join(unique_files) + "\n"
            ext = "txt"
            print(output_text)
            print(f"{len(unique_files)} files across {len(seen_projects)} projects{excluded_msg}")
        elif output_format == "csv":
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["project", "file", "line", "ref", "snippet"])
            for r in formatted:
                snippet = r["data"].replace("\n", " ").strip()
                writer.writerow([r["project"], r["path"], r["startline"], r["ref"], snippet])
            output_text = buf.getvalue()
            ext = "csv"
            print(output_text)
            print(f"Found {len(formatted)} results across {len(seen_projects)} projects{excluded_msg}")
        else:
            lines = []
            for r in formatted:
                location = f"{r['full_path']}:{r['startline']}"
                snippet = r["data"]
                indented = "\n".join(
                    f"    {line}" for line in snippet.split("\n")
                )
                lines.append(f"{location}\n{indented}")
            output_text = "\n\n".join(lines) + "\n"
            ext = "txt"
            print(output_text)
            print(f"Found {len(formatted)} results across {len(seen_projects)} projects{excluded_msg}")

        # save to file
        cache_dir = args.out
        os.makedirs(cache_dir, exist_ok=True)

        slug = re.sub(r'[^a-z0-9]+', '-', args.search_term.lower())[:30].strip('-')
        stamp = datetime.now().strftime("%Y%m%d-%H%M")
        filename = f"search-{slug}-{stamp}.{ext}"
        out_path = os.path.join(cache_dir, filename)

        with open(out_path, "w") as f:
            f.write(output_text)

        # symlink latest
        link_name = f"last_search.{ext}"
        link_path = os.path.join(cache_dir, link_name)
        if os.path.islink(link_path) or os.path.exists(link_path):
            os.remove(link_path)
        os.symlink(out_path, link_path)

        print(f"Results saved to {out_path}")
        print(f"Symlinked: {link_name} -> {filename}")
