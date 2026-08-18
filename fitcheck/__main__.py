"""CLI entry point for Fitcheck."""

import sys
from .agent import evaluate_job


def main():
    """Run job evaluation from command line."""
    if len(sys.argv) < 2:
        print("Usage: python -m fitcheck '<job description>'")
        print("   or: python -m fitcheck @file.txt")
        sys.exit(1)
    
    jd_input = sys.argv[1]
    
    # Check if input is a file reference
    if jd_input.startswith("@"):
        filepath = jd_input[1:]
        try:
            with open(filepath) as f:
                job_description = f.read()
        except FileNotFoundError:
            print(f"Error: File not found: {filepath}")
            sys.exit(1)
    else:
        job_description = jd_input
    
    print("Evaluating job description...\n")
    
    result = evaluate_job(job_description)
    
    # Print formatted output
    print("=" * 60)
    print(f"DECISION: {result['decision']}")
    print(f"SCORE: {result['score']}/5")
    print(f"RATIONALE: {result['rationale']}")
    print("=" * 60)
    
    if result.get("role_info"):
        print("\nROLE INFO:")
        ri = result["role_info"]
        print(f"  Title: {ri.get('title', 'N/A')}")
        print(f"  Level: {ri.get('level', 'N/A')}")
        print(f"  Company: {ri.get('company', 'N/A')}")
        print(f"  Location: {ri.get('location', 'N/A')}")
        print(f"  Comp: {ri.get('listed_comp', 'Not listed')}")
    
    if result.get("evidence_map"):
        print("\nEVIDENCE MAPPING:")
        for i, mapping in enumerate(result["evidence_map"].get("mappings", []), 1):
            evidence = mapping.get("evidence", "gap")
            must_have = mapping.get("must_have", "")
            if evidence == "gap":
                trainable = mapping.get("trainable_30d", False)
                status = "(trainable 30d)" if trainable else "(hard gap)"
                print(f"  {i}. {must_have}")
                print(f"     → GAP {status}")
            else:
                print(f"  {i}. {must_have}")
                print(f"     → {evidence}")
    
    if result.get("banned_check"):
        bc = result["banned_check"]
        if not bc.get("clean", True):
            print("\n⚠️  BANNED CLAIMS DETECTED:")
            for violation in bc.get("violations", []):
                print(f"  - {violation}")
    
    print(f"\nNEXT ACTION:")
    print(f"  {result['next_action']}")
    print()


if __name__ == "__main__":
    main()
