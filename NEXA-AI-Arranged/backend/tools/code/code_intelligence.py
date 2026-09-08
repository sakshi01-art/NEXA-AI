import ast
import re
import os
import json
import subprocess
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import asyncio

class CodeIntelligenceEngine:
    """
    Advanced code analysis, refactoring, bug detection,
    and intelligent code generation engine
    """
    
    def __init__(self, ai_provider):
        self.ai = ai_provider
        self.supported_languages = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'react',
            '.tsx': 'react-typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'golang',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.sh': 'bash',
            '.yaml': 'yaml',
            '.json': 'json',
            '.md': 'markdown'
        }
        self.analysis_cache = {}
    
    async def analyze_project(self, project_path: str) -> Dict:
        """Deep analysis of entire project"""
        
        try:
            project_path = Path(project_path)
            
            if not project_path.exists():
                return {'success': False, 'error': 'Project path not found'}
            
            results = {
                'path': str(project_path),
                'name': project_path.name,
                'structure': {},
                'languages': {},
                'metrics': {},
                'issues': [],
                'suggestions': [],
                'dependencies': {},
                'complexity_score': 0,
                'maintainability_score': 0,
                'security_issues': []
            }
            
            # Scan files
            all_files = []
            for ext in self.supported_languages:
                all_files.extend(project_path.rglob(f'*{ext}'))
            
            # Filter out node_modules, venv, etc.
            excluded = {
                'node_modules', '.git', '__pycache__',
                'venv', '.env', 'dist', 'build', '.next'
            }
            
            all_files = [
                f for f in all_files
                if not any(exc in f.parts for exc in excluded)
            ]
            
            # Analyze each file
            file_analyses = []
            total_lines = 0
            language_counts = {}
            
            for file_path in all_files[:50]:  # Limit to 50 files
                analysis = await self.analyze_file(str(file_path))
                
                if analysis['success']:
                    file_analyses.append(analysis)
                    total_lines += analysis.get('metrics', {}).get('lines', 0)
                    
                    lang = analysis.get('language', 'unknown')
                    language_counts[lang] = language_counts.get(lang, 0) + 1
            
            # Build project structure tree
            results['structure'] = self._build_tree(project_path)
            
            # Language distribution
            results['languages'] = language_counts
            
            # Aggregate metrics
            results['metrics'] = {
                'total_files': len(all_files),
                'analyzed_files': len(file_analyses),
                'total_lines': total_lines,
                'average_file_size': total_lines // max(len(file_analyses), 1),
                'languages_count': len(language_counts)
            }
            
            # Collect all issues
            for fa in file_analyses:
                for issue in fa.get('issues', []):
                    issue['file'] = fa.get('path', '')
                    results['issues'].append(issue)
            
            # Calculate scores
            results['complexity_score'] = self._calculate_complexity_score(file_analyses)
            results['maintainability_score'] = self._calculate_maintainability(file_analyses)
            
            # Detect dependencies
            results['dependencies'] = await self._detect_dependencies(project_path)
            
            # Check for security issues
            results['security_issues'] = await self._check_security(file_analyses)
            
            # Generate AI suggestions
            results['suggestions'] = await self._generate_project_suggestions(results)
            
            return {'success': True, 'analysis': results}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def analyze_file(self, file_path: str) -> Dict:
        """Analyze a single code file"""
        
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {'success': False, 'error': 'File not found'}
            
            # Check cache
            mtime = file_path.stat().st_mtime
            cache_key = f"{file_path}_{mtime}"
            
            if cache_key in self.analysis_cache:
                return self.analysis_cache[cache_key]
            
            # Read content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            ext = file_path.suffix.lower()
            language = self.supported_languages.get(ext, 'unknown')
            
            result = {
                'success': True,
                'path': str(file_path),
                'language': language,
                'content': content,
                'metrics': self._calculate_metrics(content),
                'issues': [],
                'functions': [],
                'classes': [],
                'imports': [],
                'complexity': 0,
                'quality_score': 0
            }
            
            # Language-specific analysis
            if language == 'python':
                result.update(self._analyze_python(content))
            elif language in ['javascript', 'typescript']:
                result.update(self._analyze_javascript(content))
            
            # Common analysis
            result['issues'].extend(self._detect_common_issues(content, language))
            result['quality_score'] = self._calculate_quality_score(result)
            
            # Cache result
            self.analysis_cache[cache_key] = result
            
            return result
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _analyze_python(self, content: str) -> Dict:
        """Deep Python code analysis"""
        
        result = {
            'functions': [],
            'classes': [],
            'imports': [],
            'issues': []
        }
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Extract functions
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'args': [a.arg for a in node.args.args],
                        'has_docstring': (
                            isinstance(node.body[0], ast.Expr) and
                            isinstance(node.body[0].value, ast.Constant)
                            if node.body else False
                        ),
                        'complexity': self._calculate_cyclomatic_complexity(node)
                    }
                    result['functions'].append(func_info)
                    
                    # Check for issues
                    if not func_info['has_docstring']:
                        result['issues'].append({
                            'type': 'warning',
                            'message': f"Function '{node.name}' missing docstring",
                            'line': node.lineno,
                            'severity': 'low'
                        })
                    
                    if func_info['complexity'] > 10:
                        result['issues'].append({
                            'type': 'complexity',
                            'message': f"Function '{node.name}' has high complexity ({func_info['complexity']})",
                            'line': node.lineno,
                            'severity': 'high',
                            'suggestion': 'Consider breaking into smaller functions'
                        })
                
                # Extract classes
                elif isinstance(node, ast.ClassDef):
                    result['classes'].append({
                        'name': node.name,
                        'line': node.lineno,
                        'methods': [
                            n.name for n in node.body
                            if isinstance(n, ast.FunctionDef)
                        ]
                    })
                
                # Extract imports
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        result['imports'].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    result['imports'].append(node.module or '')
            
            # Check for security issues
            security_issues = self._check_python_security(content)
            result['issues'].extend(security_issues)
            
        except SyntaxError as e:
            result['issues'].append({
                'type': 'error',
                'message': f'Syntax error: {str(e)}',
                'line': e.lineno,
                'severity': 'critical'
            })
        
        return result
    
    def _analyze_javascript(self, content: str) -> Dict:
        """JavaScript/TypeScript code analysis"""
        
        result = {
            'functions': [],
            'classes': [],
            'imports': [],
            'issues': []
        }
        
        # Extract functions using regex (simplified)
        func_pattern = r'(?:function|const|let|var)\s+(\w+)\s*(?:=\s*(?:async\s+)?(?:\([^)]*\)|\w+)\s*=>|\([^)]*\)\s*\{)'
        matches = re.finditer(func_pattern, content)
        
        for match in matches:
            result['functions'].append({
                'name': match.group(1),
                'line': content[:match.start()].count('\n') + 1
            })
        
        # Extract imports
        import_pattern = r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
        imports = re.findall(import_pattern, content)
        result['imports'] = imports
        
        # Check for common issues
        if 'console.log' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'console.log' in line:
                    result['issues'].append({
                        'type': 'warning',
                        'message': 'console.log found in production code',
                        'line': i + 1,
                        'severity': 'low',
                        'suggestion': 'Remove console.log before deploying'
                    })
        
        # Check for var usage (prefer const/let)
        var_pattern = r'\bvar\s+\w+'
        var_matches = re.finditer(var_pattern, content)
        for match in var_matches:
            line_num = content[:match.start()].count('\n') + 1
            result['issues'].append({
                'type': 'style',
                'message': 'Use const or let instead of var',
                'line': line_num,
                'severity': 'low'
            })
        
        return result
    
    def _calculate_cyclomatic_complexity(self, node) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _check_python_security(self, content: str) -> List[Dict]:
        """Check for Python security vulnerabilities"""
        
        issues = []
        
        security_patterns = {
            r'eval\s*\(': {
                'message': 'Dangerous eval() usage detected',
                'severity': 'critical',
                'suggestion': 'Avoid eval() - it can execute arbitrary code'
            },
            r'exec\s*\(': {
                'message': 'Dangerous exec() usage detected',
                'severity': 'critical',
                'suggestion': 'Avoid exec() - it can execute arbitrary code'
            },
            r'subprocess\.call\([^\)]*shell\s*=\s*True': {
                'message': 'Shell injection risk detected',
                'severity': 'critical',
                'suggestion': 'Use shell=False and pass args as list'
            },
            r'pickle\.load': {
                'message': 'Unsafe pickle deserialization',
                'severity': 'high',
                'suggestion': 'Pickle can execute arbitrary code - use safer alternatives'
            },
            r'password\s*=\s*["\'][^"\']+["\']': {
                'message': 'Hardcoded password detected',
                'severity': 'critical',
                'suggestion': 'Use environment variables for passwords'
            },
            r'api_key\s*=\s*["\'][^"\']+["\']': {
                'message': 'Hardcoded API key detected',
                'severity': 'critical',
                'suggestion': 'Move API keys to environment variables'
            },
            r'MD5|md5': {
                'message': 'Weak MD5 hashing algorithm',
                'severity': 'medium',
                'suggestion': 'Use SHA-256 or bcrypt for security-sensitive hashing'
            }
        }
        
        lines = content.split('\n')
        
        for pattern, info in security_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                
                issues.append({
                    'type': 'security',
                    'message': info['message'],
                    'line': line_num,
                    'severity': info['severity'],
                    'suggestion': info['suggestion'],
                    'code': lines[line_num - 1].strip()
                })
        
        return issues
    
    def _calculate_metrics(self, content: str) -> Dict:
        """Calculate code metrics"""
        
        lines = content.split('\n')
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        comment_lines = [l for l in lines if l.strip().startswith('#')]
        blank_lines = [l for l in lines if not l.strip()]
        
        return {
            'lines': len(lines),
            'code_lines': len(code_lines),
            'comment_lines': len(comment_lines),
            'blank_lines': len(blank_lines),
            'comment_ratio': len(comment_lines) / max(len(code_lines), 1),
            'characters': len(content)
        }
    
    def _detect_common_issues(self, content: str, language: str) -> List[Dict]:
        """Detect common code issues across languages"""
        
        issues = []
        lines = content.split('\n')
        
        # Long lines
        for i, line in enumerate(lines):
            if len(line) > 120:
                issues.append({
                    'type': 'style',
                    'message': f'Line too long ({len(line)} chars)',
                    'line': i + 1,
                    'severity': 'low',
                    'suggestion': 'Keep lines under 120 characters'
                })
        
        # TODO/FIXME comments
        for i, line in enumerate(lines):
            if 'TODO' in line or 'FIXME' in line or 'HACK' in line:
                issues.append({
                    'type': 'info',
                    'message': f'Found {line.strip()[:50]}',
                    'line': i + 1,
                    'severity': 'info'
                })
        
        # Debug breakpoints
        debug_patterns = ['debugger;', 'breakpoint()', 'pdb.set_trace()']
        for pattern in debug_patterns:
            if pattern in content:
                line_num = next(
                    (i + 1 for i, l in enumerate(lines) if pattern in l),
                    0
                )
                issues.append({
                    'type': 'warning',
                    'message': f'Debug breakpoint found: {pattern}',
                    'line': line_num,
                    'severity': 'medium',
                    'suggestion': 'Remove debug breakpoints before committing'
                })
        
        return issues
    
    def _calculate_quality_score(self, analysis: Dict) -> float:
        """Calculate overall code quality score (0-100)"""
        
        score = 100.0
        
        # Deduct for issues
        for issue in analysis.get('issues', []):
            severity = issue.get('severity', 'low')
            deductions = {
                'critical': 15,
                'high': 10,
                'medium': 5,
                'low': 2,
                'info': 0
            }
            score -= deductions.get(severity, 0)
        
        # Bonus for comments
        metrics = analysis.get('metrics', {})
        comment_ratio = metrics.get('comment_ratio', 0)
        
        if 0.1 <= comment_ratio <= 0.3:
            score += 5  # Good comment ratio
        
        # Check docstrings (Python)
        functions = analysis.get('functions', [])
        if functions:
            doc_ratio = sum(1 for f in functions if f.get('has_docstring')) / len(functions)
            score += doc_ratio * 10
        
        return max(0, min(100, score))
    
    def _calculate_complexity_score(self, file_analyses: List[Dict]) -> float:
        """Calculate project-wide complexity score"""
        
        if not file_analyses:
            return 0.0
        
        complexities = []
        for fa in file_analyses:
            for func in fa.get('functions', []):
                complexities.append(func.get('complexity', 1))
        
        if not complexities:
            return 0.0
        
        avg_complexity = sum(complexities) / len(complexities)
        
        # Normalize to 0-100 (lower is better)
        return max(0, 100 - avg_complexity * 10)
    
    def _calculate_maintainability(self, file_analyses: List[Dict]) -> float:
        """Calculate maintainability index"""
        
        quality_scores = [fa.get('quality_score', 0) for fa in file_analyses]
        
        if not quality_scores:
            return 0.0
        
        return sum(quality_scores) / len(quality_scores)
    
    def _build_tree(self, path: Path, depth: int = 3) -> Dict:
        """Build directory tree structure"""
        
        if depth == 0:
            return {}
        
        tree = {}
        
        try:
            for item in sorted(path.iterdir()):
                # Skip hidden and excluded directories
                excluded = {'node_modules', '.git', '__pycache__', 'venv', '.env'}
                if item.name.startswith('.') or item.name in excluded:
                    continue
                
                if item.is_dir():
                    tree[item.name] = {
                        'type': 'directory',
                        'children': self._build_tree(item, depth - 1)
                    }
                else:
                    tree[item.name] = {
                        'type': 'file',
                        'extension': item.suffix,
                        'size': item.stat().st_size
                    }
        except PermissionError:
            pass
        
        return tree
    
    async def _detect_dependencies(self, project_path: Path) -> Dict:
        """Detect project dependencies"""
        
        dependencies = {}
        
        # Python
        requirements_file = project_path / 'requirements.txt'
        if requirements_file.exists():
            with open(requirements_file) as f:
                deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            dependencies['python'] = deps
        
        pyproject_file = project_path / 'pyproject.toml'
        if pyproject_file.exists():
            dependencies['pyproject'] = 'Found pyproject.toml'
        
        # Node.js
        package_json = project_path / 'package.json'
        if package_json.exists():
            with open(package_json) as f:
                package_data = json.load(f)
            
            dependencies['nodejs'] = {
                'dependencies': list(package_data.get('dependencies', {}).keys()),
                'devDependencies': list(package_data.get('devDependencies', {}).keys()),
                'scripts': package_data.get('scripts', {})
            }
        
        # Rust
        cargo_toml = project_path / 'Cargo.toml'
        if cargo_toml.exists():
            dependencies['rust'] = 'Found Cargo.toml'
        
        # Go
        go_mod = project_path / 'go.mod'
        if go_mod.exists():
            dependencies['golang'] = 'Found go.mod'
        
        return dependencies
    
    async def _check_security(self, file_analyses: List[Dict]) -> List[Dict]:
        """Collect security issues from all files"""
        
        security_issues = []
        
        for fa in file_analyses:
            for issue in fa.get('issues', []):
                if issue.get('type') == 'security':
                    issue['file'] = fa.get('path', '')
                    security_issues.append(issue)
        
        return security_issues
    
    async def _generate_project_suggestions(self, analysis: Dict) -> List[str]:
        """Generate AI-powered project improvement suggestions"""
        
        suggestions = []
        
        # Based on metrics
        metrics = analysis.get('metrics', {})
        issues = analysis.get('issues', [])
        
        critical_count = sum(1 for i in issues if i.get('severity') == 'critical')
        high_count = sum(1 for i in issues if i.get('severity') == 'high')
        
        if critical_count > 0:
            suggestions.append(
                f"⚠️ {critical_count} critical security issues found. Immediately review and fix these."
            )
        
        if high_count > 0:
            suggestions.append(
                f"🔴 {high_count} high severity issues need attention"
            )
        
        if analysis.get('complexity_score', 100) < 50:
            suggestions.append(
                "🔧 Project complexity is high. Consider refactoring complex functions."
            )
        
        if analysis.get('maintainability_score', 100) < 60:
            suggestions.append(
                "📖 Add more documentation and comments to improve maintainability"
            )
        
        # Language-specific suggestions
        languages = analysis.get('languages', {})
        
        if 'python' in languages:
            suggestions.append("🐍 Run `pylint` or `flake8` for deeper Python analysis")
        
        if 'typescript' in languages:
            suggestions.append("📘 Enable strict TypeScript mode for better type safety")
        
        # Dependency suggestions
        deps = analysis.get('dependencies', {})
        
        if 'nodejs' in deps:
            suggestions.append("📦 Run `npm audit` to check for vulnerable dependencies")
        
        return suggestions
    
    async def fix_code(self, code: str, language: str, issue: str) -> Dict:
        """Use AI to fix code issue"""
        prompt = f"""Fix this {language} code issue:
Issue: {issue}
Code:
{code}
"""
        if hasattr(self, 'ai') and self.ai:
            try:
                response = await self.ai.complete([{"role": "user", "content": prompt}])
                return {"fixed_code": response.get("content", code), "explanation": "Code fixed by AI"}
            except Exception as e:
                return {"fixed_code": code, "error": str(e)}
        return {"fixed_code": code, "explanation": "AI provider not available"}
