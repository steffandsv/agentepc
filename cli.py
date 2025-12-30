import argparse
import sys
import time
from core.state import StateManager

def main():
    parser = argparse.ArgumentParser(description="Sovereign Agent Remote Control (CLI)")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Start/Set Objective
    start_parser = subparsers.add_parser("start", help="Set a new objective for the agent")
    start_parser.add_argument("objective", type=str, help="The task description (e.g., 'Open Firefox')")

    # Stop/Clear
    stop_parser = subparsers.add_parser("stop", help="Stop the current task")

    # Status
    status_parser = subparsers.add_parser("status", help="Get current agent status")

    args = parser.parse_args()
    manager = StateManager()

    if args.command == "start":
        print(f"[*] Sending objective to agent: {args.objective}")
        manager.set_objective(args.objective)
        print("[+] Objective set. Agent should pick it up shortly.")

    elif args.command == "stop":
        print("[*] Stopping agent...")
        manager.clear_objective()
        manager.update_status("STOPPED")
        print("[+] Agent requested to stop.")

    elif args.command == "status":
        state = manager.get_state()
        print(f"--- AGENT STATUS ---")
        print(f"Status:    {state.status}")
        print(f"Objective: {state.objective}")
        print(f"Last Log:  {state.last_log}")

        updated_ago = time.time() - state.last_updated
        print(f"Updated:   {updated_ago:.1f}s ago")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
