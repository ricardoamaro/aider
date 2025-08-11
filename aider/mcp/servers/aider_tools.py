import asyncio
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

try:
    from fastmcp import FastMCP
    from pydantic import BaseModel
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    FastMCP = None
    BaseModel = None

# Only create MCP server if FastMCP is available
if FASTMCP_AVAILABLE:
    # Initialize FastMCP server
    mcp = FastMCP("aider-tools")

    class FileAnalysis(BaseModel):
        path: str
        lines: int
        language: str
        complexity_score: float
        issues: List[str]
        size_bytes: int
        last_modified: str

    class TestResult(BaseModel):
        command: str
        exit_code: int
        stdout: str
        stderr: str
        duration: float
        cwd: str

    class SearchResult(BaseModel):
        file_path: str
        matches: List[str]
        total_matches: int

    @mcp.tool()
    async def analyze_file(path: str) -> FileAnalysis:
        """Analyze a source code file for complexity, issues, and metadata"""
        try:
            file_path = Path(path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            content = file_path.read_text(encoding='utf-8')
            lines = len(content.splitlines())
            
            # Get file stats
            stat = file_path.stat()
            size_bytes = stat.st_size
            last_modified = time.ctime(stat.st_mtime)
            
            # Simple language detection
            suffix = file_path.suffix.lower()
            language_map = {
                '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.go': 'go',
                '.rs': 'rust', '.rb': 'ruby', '.php': 'php', '.cs': 'csharp',
                '.swift': 'swift', '.kt': 'kotlin', '.scala': 'scala',
                '.html': 'html', '.css': 'css', '.scss': 'scss',
                '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml',
                '.xml': 'xml', '.md': 'markdown', '.sh': 'bash'
            }
            language = language_map.get(suffix, 'unknown')
            
            # Basic complexity analysis
            complexity_score = min(lines / 100.0, 10.0)  # Simple metric
            
            # Add complexity factors
            if 'class ' in content:
                complexity_score += 1
            if 'def ' in content or 'function ' in content:
                complexity_score += content.count('def ') * 0.1 + content.count('function ') * 0.1
            if 'if ' in content:
                complexity_score += content.count('if ') * 0.05
            if 'for ' in content or 'while ' in content:
                complexity_score += (content.count('for ') + content.count('while ')) * 0.1
            
            complexity_score = min(complexity_score, 10.0)
            
            # Issue detection
            issues = []
            if lines > 1000:
                issues.append("File is very large (>1000 lines)")
            if lines > 500:
                issues.append("File is large (>500 lines)")
            if 'TODO' in content:
                todo_count = content.count('TODO')
                issues.append(f"Contains {todo_count} TODO comment(s)")
            if 'FIXME' in content:
                fixme_count = content.count('FIXME')
                issues.append(f"Contains {fixme_count} FIXME comment(s)")
            if 'XXX' in content:
                xxx_count = content.count('XXX')
                issues.append(f"Contains {xxx_count} XXX comment(s)")
            if 'HACK' in content:
                hack_count = content.count('HACK')
                issues.append(f"Contains {hack_count} HACK comment(s)")
            
            # Check for potential issues
            if language == 'python':
                if 'import *' in content:
                    issues.append("Uses wildcard imports")
                if 'eval(' in content or 'exec(' in content:
                    issues.append("Uses eval() or exec() - potential security risk")
            
            return FileAnalysis(
                path=path,
                lines=lines,
                language=language,
                complexity_score=round(complexity_score, 2),
                issues=issues,
                size_bytes=size_bytes,
                last_modified=last_modified
            )
        except Exception as e:
            raise RuntimeError(f"Failed to analyze file: {e}")

    @mcp.tool()
    async def run_command(command: str, cwd: Optional[str] = None, timeout: int = 300) -> TestResult:
        """Execute a shell command and return results"""
        start_time = time.time()
        
        if cwd is None:
            cwd = os.getcwd()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            return TestResult(
                command=command,
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration=round(duration, 2),
                cwd=cwd
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                duration=timeout,
                cwd=cwd
            )
        except Exception as e:
            return TestResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Error executing command: {e}",
                duration=time.time() - start_time,
                cwd=cwd
            )

    @mcp.tool()
    async def search_codebase(
        pattern: str, 
        file_types: Optional[List[str]] = None,
        max_results: int = 50,
        case_sensitive: bool = False
    ) -> Dict[str, List[SearchResult]]:
        """Search for patterns in the codebase using regex"""
        if file_types is None:
            file_types = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', 
                         '.rb', '.php', '.cs', '.swift', '.kt', '.scala', '.html', 
                         '.css', '.scss', '.json', '.yaml', '.yml', '.xml', '.md', '.sh']
        
        results = {"matches": [], "summary": {}}
        total_files_searched = 0
        total_matches = 0
        cwd = Path.cwd()
        
        # Compile regex pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
        
        for file_path in cwd.rglob('*'):
            if file_path.is_file() and file_path.suffix in file_types:
                if total_files_searched >= 1000:  # Limit to prevent excessive scanning
                    break
                    
                try:
                    content = file_path.read_text(encoding='utf-8')
                    matches = []
                    
                    for line_num, line in enumerate(content.splitlines(), 1):
                        if regex.search(line):
                            matches.append(f"Line {line_num}: {line.strip()}")
                            total_matches += 1
                            
                            if len(matches) >= max_results:
                                break
                    
                    if matches:
                        results["matches"].append(SearchResult(
                            file_path=str(file_path.relative_to(cwd)),
                            matches=matches,
                            total_matches=len(matches)
                        ))
                    
                    total_files_searched += 1
                        
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        results["summary"] = {
            "total_files_searched": total_files_searched,
            "total_matches": total_matches,
            "files_with_matches": len(results["matches"])
        }
        
        return results

    @mcp.tool()
    async def get_repo_structure(max_depth: int = 3, show_hidden: bool = False) -> Dict[str, Any]:
        """Get the repository structure as a tree"""
        def build_tree(path: Path, current_depth: int = 0) -> Dict[str, Any]:
            if current_depth >= max_depth:
                return {"type": "directory", "truncated": True}
            
            if path.is_file():
                stat = path.stat()
                return {
                    "type": "file",
                    "size": stat.st_size,
                    "modified": time.ctime(stat.st_mtime)
                }
            elif path.is_dir():
                children = {}
                try:
                    for child in sorted(path.iterdir()):
                        if not show_hidden and child.name.startswith('.'):
                            continue
                        if child.name in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']:
                            continue
                        children[child.name] = build_tree(child, current_depth + 1)
                except PermissionError:
                    return {"type": "directory", "error": "Permission denied"}
                
                return {"type": "directory", "children": children}
            else:
                return {"type": "other"}
        
        cwd = Path.cwd()
        return {
            "root": str(cwd),
            "structure": build_tree(cwd)
        }

    @mcp.resource("file://{path}")
    async def get_file_content(path: str) -> str:
        """Get the content of a file"""
        try:
            file_path = Path(path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            
            # Security check - only allow files within current directory
            cwd = Path.cwd()
            try:
                file_path.resolve().relative_to(cwd.resolve())
            except ValueError:
                raise PermissionError(f"Access denied: {path} is outside current directory")
            
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            raise RuntimeError(f"Failed to read file: {e}")

    @mcp.resource("directory://{path}")
    async def get_directory_listing(path: str) -> str:
        """Get a listing of files in a directory"""
        try:
            dir_path = Path(path)
            if not dir_path.exists() or not dir_path.is_dir():
                raise NotADirectoryError(f"Directory not found: {path}")
            
            # Security check - only allow directories within current directory
            cwd = Path.cwd()
            try:
                dir_path.resolve().relative_to(cwd.resolve())
            except ValueError:
                raise PermissionError(f"Access denied: {path} is outside current directory")
            
            files = []
            for item in sorted(dir_path.iterdir()):
                if item.is_file():
                    stat = item.stat()
                    size = stat.st_size
                    modified = time.ctime(stat.st_mtime)
                    files.append(f"📄 {item.name} ({size} bytes, modified: {modified})")
                elif item.is_dir():
                    files.append(f"📁 {item.name}/")
            
            return "\n".join(files) if files else "Directory is empty"
        except Exception as e:
            raise RuntimeError(f"Failed to list directory: {e}")

    # Server startup function
    async def start_aider_mcp_server(port: int = 8000, host: str = "127.0.0.1"):
        """Start the aider MCP server"""
        try:
            import uvicorn
            
            config = uvicorn.Config(
                app=mcp.app,
                host=host,
                port=port,
                log_level="info"
            )
            
            server = uvicorn.Server(config)
            print(f"Starting aider MCP server on {host}:{port}")
            await server.serve()
        except ImportError:
            raise RuntimeError("uvicorn not available. Install with: pip install uvicorn")

else:
    # Fallback implementations when FastMCP is not available
    async def start_aider_mcp_server(port: int = 8000, host: str = "127.0.0.1"):
        """Fallback when FastMCP is not available"""
        raise RuntimeError(
            "FastMCP not available. Install with: pip install fastmcp uvicorn"
        )

# Utility function to check if server is available
def is_server_available() -> bool:
    """Check if the FastMCP server functionality is available"""
    return FASTMCP_AVAILABLE

if __name__ == "__main__":
    if FASTMCP_AVAILABLE:
        asyncio.run(start_aider_mcp_server())
    else:
        print("FastMCP not available. Install with: pip install fastmcp uvicorn")