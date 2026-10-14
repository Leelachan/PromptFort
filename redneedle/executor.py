"""Async execution engine for running attacks."""
import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from .target import TargetInterface


@dataclass
class AttackResult:
    attack_id: str
    attack_name: str
    category: str
    severity: str
    system_prompt: str
    turns: List[Dict[str, Any]]
    final_response: str
    execution_time_ms: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ExecutionEngine:
    def __init__(
        self, 
        target: TargetInterface,
        library: Any,
        max_concurrent: int = 5,
        verbose: bool = True
    ):
        self.target = target
        self.library = library
        self.max_concurrent = max_concurrent
        self.verbose = verbose
        self.results: List[AttackResult] = []
    
    async def _run_single_turn(self, attack, system_prompt: str) -> AttackResult:
        start = time.time()
        turns = []
        
        try:
            text = attack.get_all_texts()[0]
            response = await self.target.generate(system_prompt, text)
            
            turns.append({
                "input": text,
                "output": response["text"],
                "metadata": response["metadata"]
            })
            
            if self.verbose:
                print(f"  ✓ {attack.id}: responded in {time.time() - start:.2f}s")
            
            return AttackResult(
                attack_id=attack.id,
                attack_name=attack.name,
                category=attack.category,
                severity=attack.severity,
                system_prompt=system_prompt,
                turns=turns,
                final_response=response["text"],
                execution_time_ms=(time.time() - start) * 1000
            )
            
        except Exception as e:
            if self.verbose:
                print(f"  ✗ {attack.id}: ERROR - {str(e)}")
            return AttackResult(
                attack_id=attack.id,
                attack_name=attack.name,
                category=attack.category,
                severity=attack.severity,
                system_prompt=system_prompt,
                turns=turns,
                final_response="",
                execution_time_ms=(time.time() - start) * 1000,
                error=str(e)
            )
    
    async def _run_multi_turn(self, attack, system_prompt: str) -> AttackResult:
        start = time.time()
        turns = []
        history = []
        
        try:
            for i, turn_text in enumerate(attack.get_all_texts()):
                response = await self.target.generate(
                    system_prompt, 
                    turn_text,
                    conversation_history=history
                )
                
                turns.append({
                    "turn": i + 1,
                    "input": turn_text,
                    "output": response["text"],
                    "metadata": response["metadata"]
                })
                
                history.append({"role": "user", "content": turn_text})
                history.append({"role": "assistant", "content": response["text"]})
                
                if self.verbose:
                    print(f"  ✓ {attack.id} turn {i+1}: responded")
            
            return AttackResult(
                attack_id=attack.id,
                attack_name=attack.name,
                category=attack.category,
                severity=attack.severity,
                system_prompt=system_prompt,
                turns=turns,
                final_response=turns[-1]["output"] if turns else "",
                execution_time_ms=(time.time() - start) * 1000
            )
            
        except Exception as e:
            if self.verbose:
                print(f"  ✗ {attack.id}: ERROR at turn {len(turns)+1} - {str(e)}")
            return AttackResult(
                attack_id=attack.id,
                attack_name=attack.name,
                category=attack.category,
                severity=attack.severity,
                system_prompt=system_prompt,
                turns=turns,
                final_response=turns[-1]["output"] if turns else "",
                execution_time_ms=(time.time() - start) * 1000,
                error=str(e)
            )
    
    async def _run_attack(self, attack, system_prompt: str, semaphore: asyncio.Semaphore):
        async with semaphore:
            if self.verbose:
                print(f"→ Running {attack.id} ({attack.category})")
            
            if attack.is_multiturn:
                return await self._run_multi_turn(attack, system_prompt)
            else:
                return await self._run_single_turn(attack, system_prompt)
    
    async def run_all(
        self, 
        system_prompt: str,
        filter_categories: Optional[List[str]] = None,
        filter_severities: Optional[List[str]] = None
    ) -> List[AttackResult]:
        attacks = self.library.filter(filter_categories, filter_severities)
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        print(f"\n{'='*60}")
        print(f"RED NEEDLE EXECUTION")
        print(f"Target: {self.target.name}")
        print(f"Attacks: {len(attacks)}")
        print(f"System prompt length: {len(system_prompt)} chars")
        print(f"{'='*60}\n")
        
        tasks = [
            self._run_attack(attack, system_prompt, semaphore)
            for attack in attacks
        ]
        
        self.results = await asyncio.gather(*tasks)
        
        successful = sum(1 for r in self.results if not r.error)
        failed = len(self.results) - successful
        
        print(f"\n{'='*60}")
        print(f"EXECUTION COMPLETE")
        print(f"Successful: {successful} | Failed: {failed}")
        print(f"{'='*60}")
        
        return self.results
    
    def save_raw_results(self, path: str):
        data = [r.to_dict() for r in self.results]
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Raw results saved to {path}")