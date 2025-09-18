# Copyright 2024 BeardedGiant
# https://github.com/bearded-giant/gitlab-tools
# Licensed under Apache License 2.0

import os
import json
import subprocess
import re
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """Handle configuration from environment variables and config files"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "gitlab-cli"
        self.config_file = self.config_dir / "config.json"
        self._config = self._load_config()
        self._detected_project = None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment variables"""
        config = {
            'gitlab_url': None,
            'gitlab_token': None,
            'project_path': None,
            'cache_dir': str(Path.home() / ".cache" / "gitlab-cli"),
            'auto_refresh_interval': 30,
            'default_format': 'friendly',  # Default output format
            'diff_view': 'unified',  # Default diff view: unified, inline, or split
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception:
                pass
        
        # Environment variables override config file
        if os.environ.get('GITLAB_URL'):
            config['gitlab_url'] = os.environ['GITLAB_URL']
        if os.environ.get('GITLAB_TOKEN'):
            config['gitlab_token'] = os.environ['GITLAB_TOKEN']
        if os.environ.get('GITLAB_PROJECT'):
            config['project_path'] = os.environ['GITLAB_PROJECT']
        if os.environ.get('GITLAB_DEFAULT_FORMAT'):
            config['default_format'] = os.environ['GITLAB_DEFAULT_FORMAT']
        
        return config
    
    def _detect_project_from_git(self) -> Optional[str]:
        """Detect GitLab project path from git remote URL"""
        if self._detected_project is not None:
            return self._detected_project
            
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                remote_url = result.stdout.strip()
                
                # Only auto-detect if the remote URL matches our configured GitLab URL
                if self.gitlab_url:
                    # Extract domain from gitlab_url
                    import urllib.parse
                    gitlab_domain = urllib.parse.urlparse(self.gitlab_url).netloc
                    
                    # Check if remote URL contains our GitLab domain
                    if gitlab_domain not in remote_url:
                        self._detected_project = ""  # Not our GitLab instance
                        return None
                
                # Match SSH format: git@gitlab.com:group/project.git or with nested groups
                # Handles: git@gitlab.rechargeapps.net:engineering/merchant-analytics/merchant-analytics.git
                ssh_match = re.match(r'git@[^:]+:(.+?)(?:\.git)?$', remote_url)
                if ssh_match:
                    self._detected_project = ssh_match.group(1)
                    return self._detected_project
                
                # Match HTTPS format: https://gitlab.com/group/project.git or with nested groups
                https_match = re.match(r'https?://[^/]+/(.+?)(?:\.git)?/?$', remote_url)
                if https_match:
                    self._detected_project = https_match.group(1)
                    return self._detected_project
                    
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        self._detected_project = ""  # Cache negative result
        return None
    
    def save_config(self, **kwargs):
        """Save configuration to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Update current config
        self._config.update(kwargs)
        
        # Don't save token to file for security
        config_to_save = {k: v for k, v in self._config.items() if k != 'gitlab_token'}
        
        with open(self.config_file, 'w') as f:
            json.dump(config_to_save, f, indent=2)
    
    @property
    def gitlab_url(self) -> Optional[str]:
        return self._config.get('gitlab_url')
    
    @property
    def gitlab_token(self) -> Optional[str]:
        return self._config.get('gitlab_token')
    
    @property
    def project_path(self) -> Optional[str]:
        # Priority: Environment variable > Config file > Git remote detection
        project = self._config.get('project_path')
        if not project:
            project = self._detect_project_from_git()
        return project
    
    @property
    def cache_dir(self) -> str:
        return self._config.get('cache_dir', str(Path.home() / ".cache" / "gitlab-cli"))
    
    @property
    def default_format(self) -> str:
        return self._config.get('default_format', 'friendly')
    
    @property
    def diff_view(self) -> str:
        return self._config.get('diff_view', 'unified')
    
    def validate(self) -> tuple[bool, str]:
        """Validate required configuration"""
        if not self.gitlab_url:
            return False, "GITLAB_URL not set. Set via environment variable or run: gitlab-cli config --gitlab-url <url>"
        if not self.gitlab_token:
            return False, "GITLAB_TOKEN not set. Set via environment variable or run: export GITLAB_TOKEN=<token>"
        if not self.project_path:
            # Check if we're in a git repo but it's not a GitLab repo
            try:
                result = subprocess.run(
                    ['git', 'remote', 'get-url', 'origin'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    remote_url = result.stdout.strip()
                    import urllib.parse
                    gitlab_domain = urllib.parse.urlparse(self.gitlab_url).netloc
                    
                    if gitlab_domain not in remote_url:
                        if 'github.com' in remote_url:
                            return False, f"This is a GitHub repository. GitLab CLI is configured for {gitlab_domain}.\nMove to a GitLab repository or set GITLAB_PROJECT explicitly."
                        else:
                            remote_domain = re.search(r'[@/]([^/:]+)[:/]', remote_url)
                            remote_host = remote_domain.group(1) if remote_domain else 'unknown'
                            return False, f"Git remote points to {remote_host} but GitLab CLI is configured for {gitlab_domain}.\nMove to a GitLab repository or set GITLAB_PROJECT explicitly."
            except:
                pass
            
            return False, "GITLAB_PROJECT not set. Set via environment variable or run: gitlab-cli config --project <path>"
        return True, "Configuration valid"
    
    def get_cache_path(self, filename: str) -> Path:
        """Get path for cache file"""
        cache_dir = Path(self.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / filename