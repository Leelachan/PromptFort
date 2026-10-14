#!/usr/bin/env python3
"""CLI entry point for PromptFort."""
import asyncio
import argparse
import os
from pathlib import Path

from promptfort.config import PRESETS
from promptfort.target import create_target
from promptfort.executor import ExecutionEngine
from promptfort.judge import Judge, LLMJudge
from promptfort.reporter import HTMLReporter


async def main():
    parser = argparse.ArgumentParser(description="PromptFort — Prompt Red-Team Security Toolkit")
    parser.add_argument("--system-prompt", "-s", required=True, help="Path to system prompt file")
    parser.add_argument("--attacks", "-a", default="attacks/library.yaml", help="Path to attack library")
    parser.add_argument("--target", "-t", default="gpt-4", choices=list(PRESETS.keys()), help="Target model")
    parser.add_argument("--judge", "-j", default=None, help="Judge model (defaults to same as target)")
    parser.add_argument("--output", "-o", default="report.html", help="Output report path")
    parser.add_argument("--categories", "-c", nargs="+", help="Filter by categories")
    parser.add_argument("--max-concurrent", type=int, default=5, help="Max concurrent requests")
    parser.add_argument("--save-raw", help="Save raw results JSON path")
    
    args = parser.parse_args()
    
    with open(args.system_prompt, 'r') as f:
        system_prompt = f.read().strip()
    
    print(f"Loaded system prompt ({len(system_prompt)} chars)")
    
    library = AttackLibrary.from_yaml(args.attacks)
    print(f"Loaded {len(library)} attacks in {len(library.categories)} categories")
    
    target_config = PRESETS[args.target]
    target = create_target(target_config, rate_limit=True)
    print(f"Target: {target.name}")
    
    judge_target = None
    if args.judge:
        judge_config = PRESETS.get(args.judge, PRESETS[args.target])
        judge_target = create_target(judge_config, rate_limit=True)
        print(f"Judge: {judge_target.name}")
    
    engine = ExecutionEngine(target, library, max_concurrent=args.max_concurrent)
    results = await engine.run_all(
        system_prompt=system_prompt,
        filter_categories=args.categories
    )
    
    if args.save_raw:
        engine.save_raw_results(args.save_raw)
    
    llm_judge = LLMJudge(judge_target) if judge_target else None
    judge = Judge(llm_judge=llm_judge)
    scores = await judge.evaluate_all(results, system_prompt)
    
    reporter = HTMLReporter()
    reporter.save(
        path=args.output,
        results=results,
        scores=scores,
        system_prompt=system_prompt,
        target_name=target.name
    )
    
    overall = judge.get_overall_score()
    print(f"\n{'='*60}")
    print(f"FINAL SCORE: {overall.get('robustness_score', 0):.1%}")
    print(f"{'='*60}")
    print(f"Fully Resisted:      {overall.get('fully_resistant', 0)}")
    print(f"Resisted + Leaked:   {overall.get('resistant_but_leaked', 0)}")
    print(f"Partially Vulnerable:{overall.get('partially_vulnerable', 0)}")
    print(f"Fully Vulnerable:    {overall.get('fully_vulnerable', 0)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())