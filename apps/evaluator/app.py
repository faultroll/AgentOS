"""Evaluator App — Background Service

A background daemon App meant to run periodically or triggered by CLI.
It reads Telemetry or other App memory traces and uses LLM-as-Judge
to grade performance, maintaining the Pure OS / App separation.
"""
from langgraph.graph import StateGraph, END
from kernel.state import ProcessState
import time
import os

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "evaluator.md")

def build_app():
    def execute_eval(state: ProcessState) -> dict:
        print("\n🔎 [Evaluator Service] Running background LLM-as-Judge evaluation...")
        
        # Load the prompt (just simulation for now)
        try:
            with open(_PROMPT_PATH, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
        except:
            prompt_content = "Default Eval Prompt"

        # Simulating LLM call for evaluation based on Telemetry
        time.sleep(1)
        
        evaluation_result = {
            "timestamp": time.time(),
            "target": "OS-Telemetry",
            "scores": {
                "instruction_following": 9,
                "efficiency": 8,
                "safety": 10
            },
            "summary": "System operating nominally. All apps within governance limits."
        }
        
        print(f"📊 [Evaluator Service] Evaluation Complete: {evaluation_result['scores']}")

        # Evaluator app returns its JSON block so cli/api can render or store it
        return {
            "app_state": {"final_response": evaluation_result},
            "is_finished": True
        }

    workflow = StateGraph(ProcessState)
    workflow.add_node("evaluate", execute_eval)
    workflow.set_entry_point("evaluate")
    workflow.add_edge("evaluate", END)
    
    return workflow.compile()
