"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

    ArtTexts Module
    ===============

    This module provides ASCII art branding logos for the PKScreener console
    application. These art texts serve as the visual branding identity of the
    software.

    IMPORTANT USAGE TERMS:
    ----------------------
    1. These art texts are protected under the MIT License terms
    2. The trade marks "PKScreener" and the Indian flag emoji (🇮🇳) must always
       accompany the art texts when being used on the console app or as part
       of any shareable report.
    3. The UPI payment information (PKScreener@APL) must remain visible
    4. Art texts other than the ones listed in this file should be avoided,
       even though the source is released under MIT license.

    Available Art Styles:
    --------------------
    - artText_ansiRegular: Standard ANSI text style
    - artText_Merlin1: Merlin-style ASCII art
    - artText_dos_rebel: DOS rebel style with Indian flag
    - artText_Puffy: Puffy rounded style
    - artText_Rounded: Rounded corners style
    - artText_Standard: Standard text banner
    - artText_Varsity: Academic/varsity style
    - artText_Doh: DOH! style with creator credit
    - artText_Collosol: Collosol corporate style
    - artText_Roman: Roman/classical style
    - artText_Electronic: Electronic/digital style
    - artText_Epic: Epic banner style
    - artText_Isometric3: 3D isometric projection style
    - artText_FlowerPower: Decorative flower power style
    - artText_Impossible: Impossible geometry style

    Example:
        >>> from pkscreener.classes.ArtTexts import getArtText
        >>> banner = getArtText()
        >>> print(banner)
        # Random art text with system info and version
"""

import random


# =============================================================================
# ASCII ART TEXT CONSTANTS
# =============================================================================
# DISCLAIMER: These art texts are part of PKScreener's brand identity.
# They must be used as-is without modification, and the Indian flag emoji (🇮🇳)
# along with the UPI payment information must remain visible when displayed.
# =============================================================================

artText_ansiRegular = """
██████  ██   ██ ███████  ██████ ██████  ███████ ███████ ███    ██ ███████ ██████TM 🇮🇳
██   ██ ██  ██  ██      ██      ██   ██ ██      ██      ████   ██ ██      ██   ██
██████  █████   ███████ ██      ██████  █████   █████   ██ ██  ██ █████   ██████
██      ██  ██       ██ ██      ██   ██ ██      ██      ██  ██ ██ ██      ██   ██
██      ██   ██ ███████  ██████ ██   ██ ███████ ███████ ██   ████ ███████ ██   ██
UPI: PKScreener@APL
"""

artText_Merlin1 = """
   _______   __   ___   ________  ______    _______    _______   _______  _____  ___    _______   _______TM 🇮🇳
  |   __ "\ |/"| /  ") /"       )/" _  "\  /"      \  /"     "| /"     "|(\    \|"  \  /"     "| /"      \  
  (. |__) :)(: |/   / (:   \___/(: ( \___)|:        |(: ______)(: ______)|.\    \    |(: ______)|:        |
  |:  ____/ |    __/   \___  \   \/ \     |_____/   ) \/    |   \/    |  |: \.   \   | \/    |  |_____/   )
  (|  /     (// _  \    __/   \  //  \ _   //      /  // ___)_  // ___)_ |.  \    \. | // ___)_  //      /
 /|__/ \    |: | \  \  /" \   :)(:   _) \ |:  __   \ (:      "|(:      "||    \    \ |(:      "||:  __   \ 
(_______)   (__|  \__)(_______/  \_______)|__|  \___) \_______) \_______) \___|\____\) \_______) |__|  \___)
UPI: PKScreener@APL
"""

artText_dos_rebel = """
 ███████████  █████   ████  █████████                                                                  TM 🇮🇳
░░███░░░░░███░░███   ███░  ███░░░░░███  MADE IN INDIA (UPI: PKScreener@APL)
 ░███    ░███ ░███  ███   ░███    ░░░   ██████  ████████   ██████   ██████  ████████    ██████  ████████
 ░██████████  ░███████    ░░█████████  ███░░███░░███░░███ ███░░███ ███░░███░░███░░███  ███░░███░░███░░███
 ░███░░░░░░   ░███░░███    ░░░░░░░░███░███ ░░░  ░███ ░░░ ░███████ ░███████  ░███ ░███ ░███████  ░███ ░░░
 ░███         ░███ ░░███   ███    ░███░███  ███ ░███     ░███░░░  ░███░░░   ░███ ░███ ░███░░░   ░███
 █████        █████ ░░████░░█████████ ░░██████  █████    ░░██████ ░░██████  ████ █████░░██████  █████
░░░░░        ░░░░░   ░░░░  ░░░░░░░░░   ░░░░░░  ░░░░░      ░░░░░░   ░░░░░░  ░░░░ ░░░░░  ░░░░░░  ░░░░░
"""

artText_Puffy = """
 ___    _   _  ___                                                 
(  _`\ ( ) ( )(  _`\   MADE IN INDIA (UPI: PKScreener@APL)       TM 🇮🇳
| |_) )| |/'/'| (_(_)   ___  _ __   __     __    ___     __   _ __ 
| ,__/'| , <  `\__ \  /'___)( '__)/'__`\ /'__`\/' _ `\ /'__`\( '__)
| |    | |\`\ ( )_) |( (___ | |  (  ___/(  ___/| ( ) |(  ___/| |   
(_)    (_) (_)`\____)`\____)(_)  `\____)`\____)(_) (_)`\____)(_)
"""

artText_Rounded = """
 ______ _     _  ______                                           
(_____ (_)   | |/ _____) MADE IN INDIA (UPI: PKScreener@APL)    TM 🇮🇳
 _____) )____| ( (____   ____  ____ _____ _____ ____  _____  ____ 
|  ____/  _   _)\____ \ / ___)/ ___) ___ | ___ |  _ \| ___ |/ ___)
| |    | |  \ \ _____) | (___| |   | ____| ____| | | | ____| |    
|_|    |_|   \_|______/ \____)_|   |_____)_____)_| |_|_____)_|
"""

artText_Standard = """
 ____  _  ______  MADE IN INDIA (UPI: PKScreener@APL)  🇮🇳
|  _ \| |/ / ___|  ___ _ __ ___  ___ _ __   ___ _ __TM
| |_) | ' /\___ \ / __| '__/ _ \/ _ \ '_ \ / _ \ '__|
|  __/| . \ ___) | (__| | |  __/  __/ | | |  __/ |   
|_|   |_|\_\____/ \___|_|  \___|\___|_| |_|\___|_|
"""

artText_Varsity = """
 _______  ___  ____   ______                                                       
|_   __ \|_  ||_  _|.' ____ \  MADE IN INDIA (UPI: PKScreener@APL)              TM 🇮🇳
  | |__) | | |_/ /  | (___ \_| .---.  _ .--.  .---.  .---.  _ .--.  .---.  _ .--.  
  |  ___/  |  __'.   _.____`. / /'`\][ `/'`\]/ /__||/ /__||[ `.-. || / /_| |[ `/'`\] 
 _| |_    _| |  \ \_| \____) || \__.  | |    | \__.,| \__., | | | || \__., | |     
|_____|  |____||____|\______.''.___.'[___]    '.__.' '.__.'[___||__]'.__.'[___]
"""

artText_Doh = """
PPPPPPPPPPPPPPPPP   KKKKKKKKK    KKKKKKK   SSSSSSSSSSSSSSS                                                                                                            UPI: PKScreener@APL        TM 🇮🇳
UPI:PKScreener@APL  K:::::::K    K:::::K SS:::::::::::::::S
P::::::PPPPPP:::::P K:::::::K    K:::::KS:::::SSSSSS::::::S
PP:::::P     P:::::PK:::::::K   K::::::KS:::::S     SSSSSSS
  P::::P     P:::::P K::::::K  K:::::K  S:::::S                ccccccccccccccccrrrrr   rrrrrrrrr       eeeeeeeeeeee        eeeeeeeeeeee    nnnn  nnnnnnnn        eeeeeeeeeeee    rrrrr   rrrrrrrrr
  P::::P     P:::::P  K:::::K K:::::K   S:::::S              cc::::MADE:::::::cr::::rrr::WITH::::r    ee::::LOVE::::ee    ee:::::IN:::::ee  n:::nn:INDIA:nn    ee::::::::::::ee  r::::rrr:::::::::r
  P::::PPPPPP:::::P   K::::::K:::::K     S::::SSSS          c:::::::::::::::::cr:::::::::::::::::r  e::::::eeeee:::::ee e::::::eeeee:::::een::::::::::::::nn  e::::::eeeee:::::er::::©PKJMESRA::::r
  P:::::::::::::PP    K:::::::::::K       SS::::::SSSSS    c:::::::cccccc:::::crr::::::rrrrr::::::re::::::e     e:::::ee::::::e     e:::::enn:::::::::::::::ne::::::e     e:::::err::::::rrrrr::::::r
  P::::PPPPPPPPP      K:::::::::::K         SSS::::::::SS  c::::::c     ccccccc r:::::r     r:::::re:::::::eeeee::::::ee:::::::eeeee::::::e  n:::::nnnn:::::ne:::::::eeeee::::::e r:::::r     r:::::r
  P::::P              K::::::K:::::K           SSSSSS::::S c:::::c              r:::::r     rrrrrrre:::::::::::::::::e e:::::::::::::::::e   n::::n    n::::ne:::::::::::::::::e  r:::::r     rrrrrrr
  P::::P              K:::::K K:::::K               S:::::Sc:::::c              r:::::r            e::::::eeeeeeeeeee  e::::::eeeeeeeeeee    n::::n    n::::ne::::::eeeeeeeeeee   r:::::r
  P::::P              K:::::K  K:::::K              S:::::Sc::::::c     ccccccc r:::::r            e:::::::e           e:::::::e             n::::n    n::::ne:::::::e            r:::::r
PP::::::PP            K:::::K   K::::::KSSSSSSS     S:::::Sc:::::::cccccc:::::c r:::::r            e::::::::e          e::::::::e            n::::n    n::::ne::::::::e           r:::::r
P::::::::P            K:::::K    K:::::KS::::::SSSSSS:::::S c:::::::::::::::::c r:::::r             e::::::::eeeeeeee   e::::::::eeeeeeee    n::::n    n::::n e::::::::eeeeeeee   r:::::r
P::::::::P            K:::::K    K:::::KS:::::::::::::::S    cc:::::::::::::::c r:::::r              ee:::::::::::::e    ee:::::::::::::e    n::::n    n::::n  ee:::::::::::::e   r:::::r
PPPPPPPPPP            KKKKKKK    KKKKKKK SSSSSSSSSSSSSSS       cccccccccccccccc rrrrrrr                eeeeeeeeeeeeee      eeeeeeeeeeeeee    nnnnnn    nnnnnn    eeeeeeeeeeeeee   rrrrrrr
"""

artText_Collosol = """
8888888b.  888    d8P   .d8888b.                                                            TM 🇮🇳
888   Y88b 888   d8P   d88P  Y88b
888    888 888  d8P    Y88b.        MADE IN INDIA (UPI: PKScreener@APL)
888   d88P 888d88K      "Y888b.    .d8888b 888d888  .d88b.   .d88b.  88888b.   .d88b.  888d888
8888888P"  8888888b        "Y88b. d88P"    888P"   d8P  Y8b d8P  Y8b 888 "88b d8P  Y8b 888P"
888        888  Y88b         "888 888      888     88888888 88888888 888  888 88888888 888
888        888   Y88b  Y88b  d88P Y88b.    888     Y8b.     Y8b.     888  888 Y8b.     888
888        888    Y88b  "Y8888P"   "Y8888P 888      "Y8888   "Y8888  888  888  "Y8888  888
"""

artText_Roman = """
ooooooooo.   oooo    oooo  .oooooo..o                                                                    TM 🇮🇳
`888   `Y88. `888   .8P'  d8P'    `Y8   MADE IN INDIA (UPI: PKScreener@APL)
 888   .d88'  888  d8'    Y88bo.       .ooooo.  oooo d8b  .ooooo.   .ooooo.  ooo. .oo.    .ooooo.  oooo d8b
 888ooo88P'   88888[       `"Y8888o.  d88' `"Y8 `888""8P d88' `88b d88' `88b `888P"Y88b  d88' `88b `888""8P
 888          888`88b.         `"Y88b 888        888     888ooo888 888ooo888  888   888  888ooo888  888
 888          888  `88b.  oo     .d8P 888   .o8  888     888    .o 888    .o  888   888  888    .o  888
o888o        o888o  o888o 8""88888P'  `Y8bod8P' d888b    `Y8bod8P' `Y8bod8P' o888o o888o `Y8bod8P' d888b
"""

artText_Electronic = """
 ▄▄▄▄▄▄▄▄▄▄▄ ▄    ▄ ▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄▄ ▄▄        ▄ ▄▄▄▄▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄▄▄▄TM 🇮🇳
▐░░░░░░░░░░░▐░▌  ▐░▐░░░░░░░░░░░▐ PKScreener▐@APL░░░░░░░▐░░░░MADE IN▐INDIA░░░░░░▐░░▌      ▐░▐░░░░░░░░░░░▐░░░░░░░░░░░▌
▐░█▀▀▀▀▀▀▀█░▐░▌ ▐░▌▐░█▀▀▀▀▀▀▀▀▀▐░█▀▀▀▀▀▀▀▀▀▐░█▀▀▀▀▀▀▀█░▐░█▀▀▀▀▀▀▀▀▀▐░█▀▀▀▀▀▀▀▀▀▐░▌░▌     ▐░▐░█▀▀▀▀▀▀▀▀▀▐░█▀▀▀▀▀▀▀█░▌
▐░▌       ▐░▐░▌▐░▌ ▐░▌         ▐░▌         ▐░▌       ▐░▐░▌         ▐░▌         ▐░▌▐░▌    ▐░▐░▌         ▐░▌       ▐░▌
▐░█▄▄▄▄▄▄▄█░▐░▌░▌  ▐░█▄▄▄▄▄▄▄▄▄▐░▌         ▐░█▄▄▄▄▄▄▄█░▐░█▄▄▄▄▄▄▄▄▄▐░█▄▄▄▄▄▄▄▄▄▐░▌ ▐░▌   ▐░▐░█▄▄▄▄▄▄▄▄▄▐░█▄▄▄▄▄▄▄█░▌
▐░░░░░░░░░░░▐░░▌   ▐░░░░░░░░░░░▐░▌         ▐░░░░░░░░░░░▐░░░░░░░░░░░▐░░░░░░░░░░░▐░▌  ▐░▌  ▐░▐░░░░░░░░░░░▐░░░░░░░░░░░▌
▐░█▀▀▀▀▀▀▀▀▀▐░▌░▌   ▀▀▀▀▀▀▀▀▀█░▐░▌         ▐░█▀▀▀▀█░█▀▀▐░█▀▀▀▀▀▀▀▀▀▐░█▀▀▀▀▀▀▀▀▀▐░▌   ▐░▌ ▐░▐░█▀▀▀▀▀▀▀▀▀▐░█▀▀▀▀█░█▀▀
▐░▌         ▐░▌▐░▌           ▐░▐░▌         ▐░▌     ▐░▌ ▐░▌         ▐░▌         ▐░▌    ▐░▌▐░▐░▌         ▐░▌     ▐░▌
▐░▌         ▐░▌ ▐░▌ ▄▄▄▄▄▄▄▄▄█░▐░█▄▄▄▄▄▄▄▄▄▐░▌      ▐░▌▐░█▄▄▄▄▄▄▄▄▄▐░█▄▄▄▄▄▄▄▄▄▐░▌     ▐░▐░▐░█▄▄▄▄▄▄▄▄▄▐░▌      ▐░▌
▐░▌         ▐░▌  ▐░▐░░░░░░░░░░░▐░░░░░░░░░░░▐░▌       ▐░▐░░░░░░░░░░░▐░░░░░░░░░░░▐░▌      ▐░░▐░░░░░░░░░░░▐░▌       ▐░▌
 ▀           ▀    ▀ ▀▀▀▀▀▀▀▀▀▀▀ ▀▀▀▀▀▀▀▀▀▀▀ ▀         ▀ ▀▀▀▀▀▀▀▀▀▀▀ ▀▀▀▀▀▀▀▀▀▀▀ ▀        ▀▀ ▀▀▀▀▀▀▀▀▀▀▀ ▀         ▀ 
 """

artText_Epic = """
 _______ _       _______ _______ _______ _______ _______ _       _______ _______TM 🇮🇳
(  ____ | \    /(  ____ (  ____ (  ____ (  ____ (  ____ ( (    /(  ____ (  ____ )
| (    )|  \  / | (    \| (    \| (    )| (    \| (    \|  \  ( | (    \| (    )|
| (____)|  (_/ /| (_____| |     | (____)| (__   | (__   |   \ | | (__   | (____)|
|  _____|   _ ( (_____  | |     |     __|  __)  |  __)  | (\ \) |  __)  |     __)
| (     |  ( \ \      ) | |     | (\ (  | (     | (     | | \   | (     | (\ (   
| )     |  /  \ /\____) | (____/| ) \ \_| (____/| (____/| )  \  | (____/| ) \ \__
|/      |_/    \ _______(_______|/   \__(_______(_______|/    )_(_______|/   \__/
UPI: PKScreener@APL
"""

artText_Isometric3 = """
     @APL      ___         ___         ___         ___         ___         ___         ___         ___         ___  TM 🇮🇳
    R/  /\    /__/|       /  /\       /  /\       /  /\       /  /\       /  /\       /__/\       /  /\       /  /\    
   E/  /::\  |  |:|      /  /:/_     /  /:/      /  /::\     /  /:/_     /  /:/_      \  \:\     /  /:/_     /  /::\   
  N/  /:/\:\ |  |:|     /  /:/ /\   /  /:/      /  /:/\:\   /  /:/ /\   /  /:/ /\      \  \:\   /  /:/ /\   /  /:/\:\  
 E/  /:/~/:__|  |:|    /  /:/ /::\ /  /:/  ___ /  /:/~/:/  /  /:/ /:/_ /  /:/ /:/_ _____\__\:\ /  /:/ /:/_ /  /:/~/:/  
E/__/:/ /:/__/\_|:|___/__/:/ /:/\:/__/:/  /  //__/:/ /:/__/__/:/ /:/ //__/:/ /:/ //__/::::::::/__/:/ /:/ //__/:/ /:/___
R\  \:\/:/\  \:\/:::::\  \:\/:/~/:\  \:\ /  /:\  \:\/:::::\  \:\/:/ /:\  \:\/:/ /:\  \:\~~\~~ \  \:\/:/ /:\  \:\/::::::/ 
 C\  \::/  \  \::/~~~~ \  \::/ /:/ \  \:\  /:/ \  \::/~~~~ \  \::/ /:/ \  \::/ /:/ \  \:\  ~~~ \  \::/ /:/ \  \::/~~~~/  
  S\  \:\   \  \:\      \__\/ /:/   \  \:\/:/   \  \:\      \  \:\/:/   \  \:\/:/   \  \:\      \  \:\/:/   \  \:\     
   K\  \:\   \  \:\       /__/:/     \  \::/     \  \:\      \  \::/     \  \::/     \  \:\      \  \::/     \  \:\    
    P\__\/    \__\/       \__\/       \__\/       \__\/       \__\/       \__\/       \__\/       \__\/       \__\/    
"""

artText_FlowerPower = """
.-------..--.   .--.    .-'''-.    _______  .-------.       .-''-.     .-''-. ,---.   .--.   .-''-. .-------. TM 🇮🇳
\  _(`)_ |  | _/  /    / _     \  /   __  \ |  _ _   \    .'_ _   \  .'_ _   \|    \  |  | .'_ _   \|  _ _   \    
| (_ o._)| (`' ) /    (`' )/`--' | ,_/  \__)| ( ' )  |   / ( ` )   '/ ( ` )   |  ,  \ |  |/ ( ` )   | ( ' )  |    
|  (_,_) |(_ ()_)    (_ o _).  ,-./  )      |(_ o _) /  . (_ o _)  . (_ o _)  |  |\_ \|  . (_ o _)  |(_ o _) /    
|   '-.-'| (_,_)   __ (_,_). '.\  '_ '`)    | (_,_).' __|  (_,_)___|  (_,_)___|  _( )_\  |  (_,_)___| (_,_).' __  
|   |    |  |\ \  |  .---.  \  :> (_)  )  __|  |\ \  |  '  \   .---'  \   .---| (_ o _)  '  \   .---|  |\ \  |  | 
|   |    |  | \ `'   \    `-'  (  .  .-'_/  |  | \ `'   /\  `-'    /\  `-'    |  (_,_)\  |\  `-'    |  | \ `'   / 
/   )    |  |  \    / \       / `-'`-'     /|  |  \    /  \       /  \       /|  |    |  | \       /|  |  \    /  
`---'    `--'   `'-'   `-...-'    `._____.' ''-'   `'-'    `'-..-'    `'-..-' '--'    '--'  `'-..-' ''-'   `'-'   
UPI: PKScreener@APL
"""

artText_Impossible = """
         @APL       _           _            _            _          _           _           _            _           _   TM 🇮🇳
        R/\ \      /\_\        / /\        /\ \          /\ \       /\ \        /\ \        /\ \     _   /\ \        /\ \    
       E/  \ \    / / /  _    / /  \      /  \ \        /  \ \     /  \ \      /  \ \      /  \ \   /\_\/  \ \      /  \ \   
      N/ /\ \ \  / / /  /\_\ / / /\ \__  / /\ \ \      / /\ \ \   / /\ \ \    / /\ \ \    / /\ \ \_/ / / /\ \ \    / /\ \ \  
     E/ / /\ \_\/ / /__/ / // / /\ \___\/ / /\ \ \    / / /\ \_\ / / /\ \_\  / / /\ \_\  / / /\ \___/ / / /\ \_\  / / /\ \_\ 
    E/ / /_/ / / /\_____/ / \ \ \ \/___/ / /  \ \_\  / / /_/ / // /_/_ \/_/ / /_/_ \/_/ / / /  \/____/ /_/_ \/_/ / / /_/ / / 
   R/ / /__\/ / /\_______/   \ \ \    / / /    \/_/ / / /__\/ // /____/\   / /____/\   / / /    / / / /____/\   / / /__\/ /  
  C/ / /_____/ / /\ \ \  _MADE\ \ \IN/ / /INDIA    / / /_____// /\____\/  / /\____\/  / / /    / / / /\____\/  / / /_____/   
 S/ / /     / / /  \ \ \/_/\__/ / / / / /________ / / /\ \ \ / / /______ / / /______ / / /    / / / / /______ / / /\ \ \     
K/ / /     / / /    \ \ \ \/___/ / / / /_________/ / /  \ \ / / /_______/ / /_______/ / /    / / / / /_______/ / /  \ \ \    
P\/_/      \/_/      \_\_\_____\/  \/____________\/_/    \_\ /__________\/__________\/_/     \/_/\/__________\/_/    \_\/    
"""


def getArtText() -> str:
    """
    Retrieve a randomly selected ASCII art banner with system information and version.
    
    This function selects a random art text from the collection of available ASCII art
    styles, then appends the system platform name and PKScreener version number.
    The collection is shuffled and duplicated to ensure variety on repeated calls.
    
    Usage Terms:
    ------------
    1. These art texts are protected under the MIT License terms
    2. The trade marks "PKScreener" and the Indian flag emoji (🇮🇳) must always
       accompany the art texts when being used on the console app or as part
       of any shareable report.
    3. The UPI payment information (PKScreener@APL) must remain visible
    4. Art texts other than the ones listed in this file should be avoided,
       even though the source is released under MIT license.
    
    Returns:
        str: A formatted string containing:
            - Randomly selected ASCII art banner
            - System platform name (e.g., "Linux", "Windows", "Darwin")
            - PKScreener version number
            
    Example:
        >>> banner = getArtText()
        >>> print(banner)
        # Displays something like:
        # ██████  ██   ██ ███████  ██████ ██████  ███████ ███████ ███    ██ ███████ ██████TM 🇮🇳
        # ██   ██ ██  ██  ██      ██      ██   ██ ██      ██      ████   ██ ██      ██   ██
        # ...
        # Linux | v3.0.0
        
    Notes:
        - The art texts collection is shuffled and duplicated to randomize selection
        - The function imports PKSystem and VERSION dynamically to avoid circular imports
        - The returned string includes the system platform and version as a suffix
    """
    # See the terms of usage of these art texts at the top of this file
    # under comments section.
    
    # Collection of all available ASCII art banners
    artTexts = [
        artText_ansiRegular,
        artText_Merlin1,
        artText_dos_rebel,
        artText_Puffy,
        artText_Rounded,
        artText_Standard,
        artText_Varsity,
        artText_Collosol,
        artText_Roman,
        artText_Electronic,
        artText_Epic,
        artText_Isometric3,
        artText_FlowerPower,
        artText_Impossible
    ]
    
    # Duplicate the collection to increase variety on random selection
    artTexts.extend(artTexts)
    
    # Shuffle the collection for true randomness
    random.shuffle(artTexts)
    
    # Import system detection and version modules (done here to avoid circular imports)
    from PKDevTools.classes.System import PKSystem
    from pkscreener.classes import VERSION
    
    # Get system platform information
    sysName, _, _, _, _ = PKSystem.get_platform()
    
    # Return a random art text with system info and version number
    return f"{random.choice(artTexts)}{sysName} | v{VERSION}"