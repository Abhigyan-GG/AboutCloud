"""
COMPLETE PHASE INTEGRATION TEST

Runs all three phase verifications sequentially and confirms compatibility.
This validates that Phase 3 doesn't break Phase 1 or Phase 2.
"""

import sys
import os
import subprocess
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class PhaseVerificationSuite:
    """Run all phase verifications"""

    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_phase(self, phase_num: int, script_name: str) -> bool:
        """
        Run a phase verification script.

        Args:
            phase_num: Phase number (1, 2, 3)
            script_name: Script filename

        Returns:
            True if passed, False if failed
        """

        print(f"\n{'=' * 80}")
        print(f"Running PHASE {phase_num} Verification: {script_name}".center(80))
        print(f"{'=' * 80}\n")

        try:
            result = subprocess.run(
                [sys.executable, script_name],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=False,
            )

            passed = result.returncode == 0
            self.results[phase_num] = {
                'passed': passed,
                'script': script_name,
                'exit_code': result.returncode,
            }

            return passed

        except Exception as e:
            print(f"❌ Error running {script_name}: {e}")
            self.results[phase_num] = {
                'passed': False,
                'script': script_name,
                'error': str(e),
            }
            return False

    def verify_compatibility(self) -> bool:
        """
        Verify that all phases are compatible.

        Returns:
            True if all compatible, False otherwise
        """

        print(f"\n{'=' * 80}")
        print("COMPATIBILITY CHECK".center(80))
        print(f"{'=' * 80}\n")

        all_passed = all(r['passed'] for r in self.results.values())

        if all_passed:
            print("✅ All phases passed independently")
            print("✅ No breaking changes detected")
            return True
        else:
            failed_phases = [p for p, r in self.results.items() if not r['passed']]
            print(f"❌ Failed phases: {failed_phases}")
            return False

    def print_summary(self):
        """Print final summary"""

        total_duration = (self.end_time - self.start_time).total_seconds()

        print(f"\n{'=' * 80}")
        print("INTEGRATION TEST SUMMARY".center(80))
        print(f"{'=' * 80}\n")

        for phase_num in sorted(self.results.keys()):
            result = self.results[phase_num]
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            print(f"  Phase {phase_num}: {status} ({result['script']})")

        print(f"\nTotal duration: {total_duration:.1f} seconds\n")

        all_passed = all(r['passed'] for r in self.results.values())

        if all_passed:
            print("=" * 80)
            print("🎉 ALL PHASES VERIFIED SUCCESSFULLY 🎉".center(80))
            print("System is ready for production deployment".center(80))
            print("=" * 80 + "\n")
            return 0
        else:
            print("=" * 80)
            print("❌ INTEGRATION TEST FAILED".center(80))
            print("Fix failures above before proceeding".center(80))
            print("=" * 80 + "\n")
            return 1


def main():
    """Run complete integration test"""

    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "COMPLETE SYSTEM INTEGRATION VERIFICATION".center(78) + "║")
    print("║" + "Phases 1, 2, and 3 Compatibility Check".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝\n")

    suite = PhaseVerificationSuite()
    suite.start_time = datetime.utcnow()

    # Run each phase
    phase1_passed = suite.run_phase(1, "verify_phase1.py")
    phase2_passed = suite.run_phase(2, "verify_phase2.py")
    phase3_passed = suite.run_phase(3, "verify_phase3.py")

    suite.end_time = datetime.utcnow()

    # Verify compatibility
    compatible = suite.verify_compatibility()

    # Print summary
    exit_code = suite.print_summary()

    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)