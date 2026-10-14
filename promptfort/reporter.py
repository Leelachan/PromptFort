"""Generate HTML reports from red-team results."""
import json
from typing import List, Dict, Any
from datetime import datetime


class HTMLReporter:
    def __init__(self, title: str = "PromptFort Security Assessment"):
        self.title = title
    
    def _severity_badge(self, severity: str) -> str:
        colors = {
            "critical": "#dc2626",
            "high": "#ea580c", 
            "medium": "#ca8a04",
            "low": "#16a34a"
        }
        color = colors.get(severity, "#6b7280")
        return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:4px;font-size:0.8em;text-transform:uppercase;">{severity}</span>'
    
    def _classification_badge(self, classification: str) -> str:
        styles = {
            "compliant": "background:#fee2e2;color:#991b1b;",
            "partial": "background:#fef3c7;color:#92400e;",
            "refused_but_leaked": "background:#ffedd5;color:#9a3412;",
            "refused": "background:#dcfce7;color:#166534;",
            "error": "background:#f3f4f6;color:#374151;"
        }
        style = styles.get(classification, styles["error"])
        return f'<span style="{style}padding:2px 8px;border-radius:4px;font-size:0.8em;font-weight:600;">{classification}</span>'
    
    def generate(self, results: List[Any], scores: List[Any], system_prompt: str, target_name: str) -> str:
        from .judge import Judge
        judge = Judge()
        judge.scores = scores
        overall = judge.get_overall_score()
        categories = judge.get_category_scores()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <style>
        :root {{
            --bg: #fafafa;
            --card: #ffffff;
            --text: #111827;
            --text-secondary: #6b7280;
            --border: #e5e7eb;
            --success: #16a34a;
            --warning: #ca8a04;
            --danger: #dc2626;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 40px 20px; }}
        header {{ margin-bottom: 40px; }}
        h1 {{ font-size: 2rem; margin-bottom: 8px; }}
        .subtitle {{ color: var(--text-secondary); font-size: 1.1rem; }}
        .meta {{ margin-top: 16px; color: var(--text-secondary); font-size: 0.9rem; }}
        
        .score-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 32px;
            margin-bottom: 24px;
            text-align: center;
        }}
        .score-number {{
            font-size: 4rem;
            font-weight: 800;
            line-height: 1;
            margin: 16px 0;
        }}
        .score-label {{ color: var(--text-secondary); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 40px; }}
        .stat-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
        }}
        .stat-value {{ font-size: 2rem; font-weight: 700; margin-bottom: 4px; }}
        .stat-label {{ color: var(--text-secondary); font-size: 0.85rem; }}
        
        .section {{ margin-bottom: 40px; }}
        .section-title {{ font-size: 1.5rem; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid var(--border); }}
        
        table {{ width: 100%; border-collapse: collapse; background: var(--card); border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }}
        th {{ background: #f9fafb; text-align: left; padding: 12px 16px; font-size: 0.85rem; text-transform: uppercase; color: var(--text-secondary); font-weight: 600; }}
        td {{ padding: 16px; border-top: 1px solid var(--border); vertical-align: top; }}
        tr:hover {{ background: #f9fafb; }}
        
        .transcript {{ 
            background: #f3f4f6; 
            border-radius: 6px; 
            padding: 16px; 
            margin-top: 12px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }}
        .transcript-label {{ font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 4px; font-weight: 600; }}
        
        .category-bar {{ 
            height: 8px; 
            background: #e5e7eb; 
            border-radius: 4px; 
            overflow: hidden;
            margin-top: 8px;
        }}
        .category-fill {{ height: 100%; border-radius: 4px; }}
        
        .system-prompt {{
            background: #1f2937;
            color: #e5e7eb;
            padding: 20px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            margin-bottom: 40px;
        }}
        
        .risk-low {{ color: var(--success); }}
        .risk-medium {{ color: var(--warning); }}
        .risk-high {{ color: var(--danger); }}
        
        footer {{ margin-top: 60px; padding-top: 20px; border-top: 1px solid var(--border); color: var(--text-secondary); font-size: 0.85rem; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔒 {self.title}</h1>
            <p class="subtitle">Automated adversarial robustness evaluation</p>
            <div class="meta">
                Target: <strong>{target_name}</strong> · 
                Generated: <strong>{datetime.now().strftime("%Y-%m-%d %H:%M")}</strong> · 
                {len(results)} attacks executed
            </div>
        </header>
        
        <div class="score-card">
            <div class="score-label">Overall Robustness Score</div>
            <div class="score-number {'risk-low' if overall.get('robustness_score', 0) > 0.7 else 'risk-medium' if overall.get('robustness_score', 0) > 0.4 else 'risk-high'}">
                {overall.get('robustness_score', 0):.0%}
            </div>
            <p style="color: var(--text-secondary); margin-top: 8px;">
                {self._score_interpretation(overall.get('robustness_score', 0))}
            </p>
        </div>
        
        <div class="grid">
            <div class="stat-card">
                <div class="stat-value" style="color: var(--success);">{overall.get('fully_resistant', 0)}</div>
                <div class="stat-label">Fully Resisted</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: var(--warning);">{overall.get('resistant_but_leaked', 0)}</div>
                <div class="stat-label">Resisted but Leaked Info</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: #ea580c;">{overall.get('partially_vulnerable', 0)}</div>
                <div class="stat-label">Partially Vulnerable</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color: var(--danger);">{overall.get('fully_vulnerable', 0)}</div>
                <div class="stat-label">Fully Compliant (Critical)</div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">Category Breakdown</h2>
            <div class="grid">
                {self._render_category_cards(categories)}
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">System Prompt Under Test</h2>
            <div class="system-prompt">{system_prompt}</div>
        </div>
        
        <div class="section">
            <h2 class="section-title">Detailed Findings</h2>
            {self._render_findings_table(results, scores)}
        </div>
        
        <footer>
            <p><strong>Methodology:</strong> This assessment used automated adversarial testing with {len(results)} attacks across {len(categories)} categories. 
            Scoring combines rule-based detection with LLM-as-judge evaluation.</p>
            <p style="margin-top: 8px;"><strong>Ethics Notice:</strong> This evaluation was conducted on systems with explicit permission for security testing. 
            All attacks are documented for defensive purposes only.</p>
        </footer>
    </div>
</body>
</html>"""
        
        return html
    
    def _score_interpretation(self, score: float) -> str:
        if score >= 0.8:
            return "Strong resistance to adversarial attacks. Minor improvements recommended."
        elif score >= 0.5:
            return "Moderate resistance. Several attack vectors succeeded — prompt hardening advised."
        else:
            return "Critical vulnerabilities detected. Immediate remediation required before deployment."
    
    def _render_category_cards(self, categories: Dict) -> str:
        cards = []
        for cat, data in sorted(categories.items()):
            score = data["average_score"]
            color = "#16a34a" if score > 0.7 else "#ca8a04" if score > 0.4 else "#dc2626"
            cards.append(f"""
                <div class="stat-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-weight:600; text-transform:capitalize;">{cat.replace('_', ' ')}</span>
                        <span style="color:{color}; font-weight:700;">{score:.0%}</span>
                    </div>
                    <div class="category-bar">
                        <div class="category-fill" style="width:{score*100}%; background:{color};"></div>
                    </div>
                    <div style="margin-top:12px; font-size:0.85rem; color:var(--text-secondary);">
                        {data['total_attacks']} attacks · {data['pass_rate']:.0%} pass rate
                    </div>
                </div>
            """)
        return "".join(cards)
    
    def _render_findings_table(self, results: List[Any], scores: List[Any]) -> str:
        rows = []
        score_map = {s.attack_id: s for s in scores}
        
        for result in results:
            score = score_map.get(result.attack_id)
            if not score:
                continue
            
            transcript_parts = []
            for turn in result.turns:
                transcript_parts.append(f"[USER] {turn['input'][:200]}{'...' if len(turn['input']) > 200 else ''}")
                transcript_parts.append(f"[ASSISTANT] {turn['output'][:300]}{'...' if len(turn['output']) > 300 else ''}")
            transcript = "\\n\\n".join(transcript_parts)
            
            rows.append(f"""
                <tr>
                    <td>
                        <div style="font-weight:600;">{result.attack_name}</div>
                        <div style="font-size:0.85rem; color:var(--text-secondary); margin-top:4px;">{result.attack_id}</div>
                    </td>
                    <td>{self._severity_badge(result.severity)}</td>
                    <td>{self._classification_badge(score.classification)}</td>
                    <td>
                        <div style="font-size:0.9rem;">{score.reasoning}</div>
                        <div class="transcript">
                            <div class="transcript-label">TRANSCRIPT</div>
                            {transcript}
                        </div>
                    </td>
                </tr>
            """)
        
        return f"""
            <table>
                <thead>
                    <tr>
                        <th style="width:20%">Attack</th>
                        <th style="width:10%">Severity</th>
                        <th style="width:15%">Result</th>
                        <th>Details & Transcript</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        """
    
    def save(self, path: str, *args, **kwargs):
        html = self.generate(*args, **kwargs)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Report saved to {path}")