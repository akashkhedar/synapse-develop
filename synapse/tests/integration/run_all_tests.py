"""
Master Test Runner
Runs all integration tests in sequence.

Run with:
    python manage.py shell < tests/integration/run_all_tests.py
    
Or individually:
    python manage.py shell < tests/integration/test_01_user_setup.py
    python manage.py shell < tests/integration/test_02_project_setup.py
    python manage.py shell < tests/integration/test_03_assignment.py
    python manage.py shell < tests/integration/test_04_honeypot.py
    python manage.py shell < tests/integration/test_05_consolidation.py
    python manage.py shell < tests/integration/test_06_expert_review.py
"""

import os
import sys
from datetime import datetime

# Set flag to prevent test modules from auto-running when imported
os.environ['SYNAPSE_TEST_IMPORT'] = '1'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.synapse')

import django
django.setup()

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'


def print_banner():
    print(f"""
{CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                                ║
║     ███████╗██╗   ██╗███╗   ██╗ █████╗ ██████╗ ███████╗        ║
║     ██╔════╝╚██╗ ██╔╝████╗  ██║██╔══██╗██╔══██╗██╔════╝        ║
║     ███████╗ ╚████╔╝ ██╔██╗ ██║███████║██████╔╝███████╗        ║
║     ╚════██║  ╚██╔╝  ██║╚██╗██║██╔══██║██╔═══╝ ╚════██║        ║
║     ███████║   ██║   ██║ ╚████║██║  ██║██║     ███████║        ║
║     ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚══════╝        ║
║                                                                ║
║              PLATFORM INTEGRATION TEST SUITE                   ║
║                                                                ║
╚══════════════════════════════════════════════════════════════╝{RESET}
""")


def run_test_module(name, description, module):
    """Run a test module and return results"""
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}Running: {description}{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}\n")
    
    try:
        if hasattr(module, 'run'):
            result = module.run()
            return result
        else:
            print(f"{RED}Module {name} has no run() function{RESET}")
            return False
    except Exception as e:
        print(f"{RED}Error running {name}: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return False


def run_all():
    """Run all test suites in order"""
    print_banner()
    
    start_time = datetime.now()
    print(f"{BLUE}Test run started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n")
    
    results = {}
    
    # Import and run each test module
    try:
        print(f"\n{CYAN}Phase 1: User Setup{RESET}")
        from tests.integration import test_01_user_setup
        results['User Setup'] = run_test_module(
            'test_01_user_setup',
            'User & Account Setup',
            test_01_user_setup
        )
    except Exception as e:
        print(f"{RED}Failed to import test_01_user_setup: {e}{RESET}")
        results['User Setup'] = False
    
    try:
        print(f"\n{CYAN}Phase 2: Project Setup{RESET}")
        from tests.integration import test_02_project_setup
        results['Project Setup'] = run_test_module(
            'test_02_project_setup',
            'Project & Task Setup',
            test_02_project_setup
        )
    except Exception as e:
        print(f"{RED}Failed to import test_02_project_setup: {e}{RESET}")
        results['Project Setup'] = False
    
    try:
        print(f"\n{CYAN}Phase 3: Assignment System{RESET}")
        from tests.integration import test_03_assignment
        results['Assignment'] = run_test_module(
            'test_03_assignment',
            'Task Assignment System',
            test_03_assignment
        )
    except Exception as e:
        print(f"{RED}Failed to import test_03_assignment: {e}{RESET}")
        results['Assignment'] = False
    
    try:
        print(f"\n{CYAN}Phase 4: Honeypot System{RESET}")
        from tests.integration import test_04_honeypot
        results['Honeypot'] = run_test_module(
            'test_04_honeypot',
            'Honeypot Evaluation System',
            test_04_honeypot
        )
    except Exception as e:
        print(f"{RED}Failed to import test_04_honeypot: {e}{RESET}")
        results['Honeypot'] = False
    
    try:
        print(f"\n{CYAN}Phase 5: Consolidation{RESET}")
        from tests.integration import test_05_consolidation
        results['Consolidation'] = run_test_module(
            'test_05_consolidation',
            'Annotation Consolidation',
            test_05_consolidation
        )
    except Exception as e:
        print(f"{RED}Failed to import test_05_consolidation: {e}{RESET}")
        results['Consolidation'] = False
    
    try:
        print(f"\n{CYAN}Phase 6: Expert Review{RESET}")
        from tests.integration import test_06_expert_review
        results['Expert Review'] = run_test_module(
            'test_06_expert_review',
            'Expert Review Workflow',
            test_06_expert_review
        )
    except Exception as e:
        print(f"{RED}Failed to import test_06_expert_review: {e}{RESET}")
        results['Expert Review'] = False
    
    # Print final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n{CYAN}{'='*60}{RESET}")
    print(f"{CYAN}                    FINAL RESULTS{RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")
    
    passed = 0
    failed = 0
    
    for name, result in results.items():
        if result:
            print(f"{GREEN}  ✓ {name}: PASSED{RESET}")
            passed += 1
        else:
            print(f"{RED}  ✗ {name}: FAILED{RESET}")
            failed += 1
    
    print(f"\n{'-'*40}")
    print(f"  Total:  {passed + failed}")
    print(f"  {GREEN}Passed: {passed}{RESET}")
    print(f"  {RED}Failed: {failed}{RESET}")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"{'-'*40}\n")
    
    if failed == 0:
        print(f"{GREEN}╔══════════════════════════════════════╗{RESET}")
        print(f"{GREEN}║     ALL TESTS PASSED! ✓              ║{RESET}")
        print(f"{GREEN}╚══════════════════════════════════════╝{RESET}\n")
    else:
        print(f"{RED}╔══════════════════════════════════════╗{RESET}")
        print(f"{RED}║     SOME TESTS FAILED! ✗             ║{RESET}")
        print(f"{RED}╚══════════════════════════════════════╝{RESET}\n")
    
    return failed == 0


if __name__ == '__main__':
    run_all()
