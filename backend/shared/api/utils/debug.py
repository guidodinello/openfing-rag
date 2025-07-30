from fastapi import APIRouter


def debug_router_dependencies(router: APIRouter, router_name: str):
    """Debug function to print router dependencies"""
    print(f"\n=== DEBUG: {router_name} Dependencies ===")
    print(f"Router dependencies: {router.dependencies}")

    for route in router.routes:
        if hasattr(route, "dependant"):
            print(f"Route: {route.path} [{getattr(route, 'methods', 'N/A')}]")
            print(f"  Dependencies: {route.dependant.dependencies}")
            for dep in route.dependant.dependencies:
                print(f"    - {dep.call}")
        print()
