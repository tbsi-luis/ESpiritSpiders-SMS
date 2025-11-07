from typing import List, Dict

RELIEVERS: List[Dict[str, str]] = [
    {
        "name": "Luis Mario Bandivas",
        "contact": "+639460371457"
    },
    {
        "name": "Xanderex Aquinde",
        "contact": "+639060158736"
    }
]

def get_relievers() -> List[Dict[str, str]]:
    return RELIEVERS