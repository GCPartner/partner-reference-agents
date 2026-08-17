import os

def create_assets():
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    os.makedirs(static_dir, exist_ok=True)
    
    svgs = {
        "tmobile.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect width="100" height="100" rx="10" fill="#E20074"/>
            <text x="50" y="70" font-family="sans-serif" font-weight="bold" font-size="60" fill="white" text-anchor="middle">T</text>
        </svg>""",
        "verizon.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect width="100" height="100" rx="10" fill="black"/>
            <path d="M20 50 L45 75 L80 30" stroke="#CD040B" stroke-width="15" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>""",
        "att.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect width="100" height="100" rx="10" fill="#00A6CA"/>
            <circle cx="50" cy="50" r="30" fill="white"/>
            <circle cx="50" cy="50" r="25" fill="#00A6CA"/>
            <line x1="25" y1="50" x2="75" y2="50" stroke="white" stroke-width="4"/>
            <line x1="30" y1="35" x2="70" y2="35" stroke="white" stroke-width="4"/>
            <line x1="30" y1="65" x2="70" y2="65" stroke="white" stroke-width="4"/>
        </svg>""",
        "carrier.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect width="100" height="100" rx="10" fill="#666666"/>
            <text x="50" y="65" font-family="sans-serif" font-weight="bold" font-size="40" fill="white" text-anchor="middle">Carrier</text>
        </svg>""",
        "pixel.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect x="25" y="10" width="50" height="80" rx="8" fill="#4285F4" stroke="#333" stroke-width="2"/>
            <rect x="29" y="14" width="42" height="66" rx="4" fill="#F3F4F6"/>
            <circle cx="50" cy="20" r="2" fill="#333"/>
            <line x1="45" y1="84" x2="55" y2="84" stroke="#333" stroke-width="2" stroke-linecap="round"/>
        </svg>""",
        "iphone.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect x="25" y="10" width="50" height="80" rx="8" fill="#999999" stroke="#333" stroke-width="2"/>
            <rect x="29" y="14" width="42" height="66" rx="4" fill="#F3F4F6"/>
            <circle cx="50" cy="20" r="2" fill="#333"/>
            <line x1="45" y1="84" x2="55" y2="84" stroke="#333" stroke-width="2" stroke-linecap="round"/>
        </svg>""",
        "samsung.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <rect x="25" y="10" width="50" height="80" rx="8" fill="#034EA2" stroke="#333" stroke-width="2"/>
            <rect x="29" y="14" width="42" height="66" rx="4" fill="#F3F4F6"/>
            <circle cx="50" cy="20" r="2" fill="#333"/>
            <line x1="45" y1="84" x2="55" y2="84" stroke="#333" stroke-width="2" stroke-linecap="round"/>
        </svg>"""
    }
    
    for filename, content in svgs.items():
        filepath = os.path.join(static_dir, filename)
        with open(filepath, "w") as f:
            f.write(content)
        print(f"Created static asset: {filepath}")

if __name__ == "__main__":
    create_assets()
