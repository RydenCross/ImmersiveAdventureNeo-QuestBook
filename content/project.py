from generator.builder import ChapterBuilder
from content.actually_additions import build_actually_additions
from content.create import build_create
from model import Project


def _build_welcome(project: Project) -> str:
    welcome = ChapterBuilder(
        project,
        slug="00_welcome",
        title="Welcome",
        icon="minecraft:book",
        description="Your first steps in Immersive Adventure Neo.",
    )

    start = (
        welcome.quest(
            "start",
            "Welcome to Immersive Adventure Neo",
            "minecraft:book",
            (
                "This questbook guides you through survival, exploration, technology, "
                "magic, and the pack's endgame. Check this quest to begin."
            ),
            0,
            0,
        )
        .checkmark()
        .reward_item("minecraft:bread", 8)
        .finish()
    )

    logs = (
        welcome.quest(
            "first_logs",
            "Gather Wood",
            "minecraft:oak_log",
            "Collect eight oak logs to begin crafting tools and building shelter.",
            2,
            -1.5,
        )
        .depends_on(start)
        .item("minecraft:oak_log", 8)
        .finish()
    )

    crafting = (
        welcome.quest(
            "crafting_table",
            "A Place to Craft",
            "minecraft:crafting_table",
            (
                "Craft a crafting table. Many recipes in the pack require more than "
                "the small player crafting grid."
            ),
            4,
            -1.5,
        )
        .depends_on(logs)
        .item("minecraft:crafting_table")
        .finish()
    )

    tools = (
        welcome.quest(
            "stone_tools",
            "Stone Age",
            "minecraft:stone_pickaxe",
            "Upgrade to a stone pickaxe to open the path to early mining and better resources.",
            6,
            -1.5,
        )
        .depends_on(crafting)
        .advancement("minecraft:story/upgrade_tools")
        .finish()
    )

    food = (
        welcome.quest(
            "food",
            "Secure a Meal",
            "minecraft:cooked_beef",
            "Keep food nearby before traveling. Obtain cooked beef as a dependable early meal.",
            2,
            1.5,
        )
        .depends_on(start)
        .item("minecraft:cooked_beef", 4)
        .reward_item("minecraft:torch", 16)
        .finish()
    )

    shelter = (
        welcome.quest(
            "shelter",
            "Prepare for the Night",
            "minecraft:white_bed",
            "Create a bed so you can establish a spawn point and safely pass dangerous nights.",
            4,
            1.5,
        )
        .depends_on(food)
        .item("minecraft:white_bed")
        .finish()
    )

    furnace = (
        welcome.quest(
            "furnace",
            "Fire and Stone",
            "minecraft:furnace",
            "Craft a furnace for cooking food and processing your first ores.",
            6,
            1.5,
        )
        .depends_on(shelter, tools)
        .item("minecraft:furnace")
        .reward_item("minecraft:coal", 8)
        .finish()
    )

    iron = (
        welcome.quest(
            "iron",
            "Acquire Hardware",
            "minecraft:iron_ingot",
            (
                "Smelt your first iron ingot. Iron marks the transition from basic "
                "survival into the wider progression of the pack."
            ),
            8,
            0,
        )
        .depends_on(furnace)
        .advancement("minecraft:story/smelt_iron")
        .finish()
    )

    return (
        welcome.quest(
            "ready",
            "Adventure Awaits",
            "minecraft:compass",
            "You understand the basics. Continue into Survival, Mining, and Exploration.",
            10,
            0,
        )
        .depends_on(iron)
        .checkmark()
        .reward_item("minecraft:golden_apple")
        .finish()
    )


def _build_survival(project: Project, welcome_complete: str) -> str:
    survival = ChapterBuilder(
        project,
        slug="01_survival",
        title="Survival",
        icon="minecraft:campfire",
        description="Build a secure home, dependable food supply, and sustainable early-game base.",
    )

    begin = (
        survival.quest(
            "begin",
            "A Life Worth Building",
            "minecraft:campfire",
            "Turn your first-night shelter into a base that can support long-term progression.",
            0,
            0,
        )
        .depends_on(welcome_complete)
        .checkmark()
        .finish()
    )

    chest = (
        survival.quest(
            "storage",
            "Organized Supplies",
            "minecraft:chest",
            "Craft storage before loose materials begin taking over your base.",
            2,
            -3,
        )
        .depends_on(begin)
        .item("minecraft:chest", 2)
        .finish()
    )
    barrel = (
        survival.quest(
            "barrel",
            "Compact Storage",
            "minecraft:barrel",
            "Barrels remain accessible with a solid block above them and fit neatly into workshops.",
            4,
            -3,
        )
        .depends_on(chest)
        .item("minecraft:barrel", 2)
        .finish()
    )
    signs = (
        survival.quest(
            "signs",
            "Label Everything",
            "minecraft:oak_sign",
            "Use signs to label storage, routes, farms, and important machines.",
            6,
            -3,
            optional=True,
        )
        .depends_on(barrel)
        .item("minecraft:oak_sign", 4)
        .finish()
    )

    shield = (
        survival.quest(
            "shield",
            "A Sturdy Defense",
            "minecraft:shield",
            "A shield can stop arrows, soften explosions, and make early combat much safer.",
            2,
            -1,
        )
        .depends_on(begin)
        .item("minecraft:shield")
        .reward_item("minecraft:arrow", 16)
        .finish()
    )
    armor = (
        survival.quest(
            "iron_armor",
            "Suit Up",
            "minecraft:iron_chestplate",
            "Craft a full set of iron armor before taking on caves and dangerous structures.",
            4,
            -1,
        )
        .depends_on(shield)
        .item("minecraft:iron_helmet")
        .item("minecraft:iron_chestplate")
        .item("minecraft:iron_leggings")
        .item("minecraft:iron_boots")
        .finish()
    )
    ranged = (
        survival.quest(
            "bow",
            "Keep Your Distance",
            "minecraft:bow",
            "A bow gives you a safe answer to creepers, skeletons, and distant threats.",
            6,
            -1,
        )
        .depends_on(armor)
        .item("minecraft:bow")
        .item("minecraft:arrow", 16)
        .finish()
    )

    wheat = (
        survival.quest(
            "wheat_farm",
            "Fields of Gold",
            "minecraft:wheat",
            "Start a wheat farm for bread, animal breeding, and several later recipes.",
            2,
            1,
        )
        .depends_on(begin)
        .item("minecraft:wheat", 16)
        .finish()
    )
    bread = (
        survival.quest(
            "bread",
            "Daily Bread",
            "minecraft:bread",
            "Turn your harvest into a renewable food supply.",
            4,
            1,
        )
        .depends_on(wheat)
        .item("minecraft:bread", 8)
        .finish()
    )
    animals = (
        survival.quest(
            "animal_husbandry",
            "Two by Two",
            "minecraft:wheat",
            "Breed a pair of animals to begin a sustainable source of food and materials.",
            6,
            1,
        )
        .depends_on(wheat)
        .advancement("minecraft:husbandry/breed_an_animal")
        .finish()
    )
    eggs = (
        survival.quest(
            "eggs",
            "The Chicken or the Egg",
            "minecraft:egg",
            "Collect eggs for food, farming, and crafting recipes.",
            8,
            1,
            optional=True,
        )
        .depends_on(animals)
        .item("minecraft:egg", 8)
        .finish()
    )

    campfire = (
        survival.quest(
            "campfire",
            "Gather Around the Fire",
            "minecraft:campfire",
            "A campfire provides light, smoke signals, and fuel-free cooking.",
            2,
            3,
        )
        .depends_on(begin)
        .item("minecraft:campfire")
        .finish()
    )
    smoker = (
        survival.quest(
            "smoker",
            "Fast Food",
            "minecraft:smoker",
            "Smokers cook food twice as quickly as a normal furnace.",
            4,
            3,
        )
        .depends_on(campfire)
        .item("minecraft:smoker")
        .finish()
    )
    cauldron = (
        survival.quest(
            "cauldron",
            "A Proper Wash Station",
            "minecraft:cauldron",
            "Keep a cauldron nearby for utility, decoration, and future crafting systems.",
            6,
            3,
            optional=True,
        )
        .depends_on(campfire)
        .item("minecraft:cauldron")
        .finish()
    )

    bucket = (
        survival.quest(
            "bucket",
            "Carry the Current",
            "minecraft:water_bucket",
            "A water bucket supports farming, safe descents, terrain control, and emergency escapes.",
            2,
            5,
        )
        .depends_on(begin)
        .item("minecraft:water_bucket")
        .finish()
    )
    infinite_water = (
        survival.quest(
            "infinite_water",
            "Endless Water",
            "minecraft:water_bucket",
            "Create a two-by-two infinite water source at your base, then confirm the task.",
            4,
            5,
        )
        .depends_on(bucket)
        .checkmark()
        .finish()
    )
    sugar = (
        survival.quest(
            "sugar_cane",
            "Paper Trail",
            "minecraft:sugar_cane",
            "Grow sugar cane near water. Paper will matter for maps, books, and enchanting.",
            6,
            5,
        )
        .depends_on(infinite_water)
        .item("minecraft:sugar_cane", 16)
        .finish()
    )
    leather = (
        survival.quest(
            "leather",
            "Tanned and Ready",
            "minecraft:leather",
            "Gather leather for books, item frames, and several utility recipes.",
            8,
            5,
        )
        .depends_on(animals)
        .item("minecraft:leather", 8)
        .finish()
    )
    books = (
        survival.quest(
            "books",
            "Knowledge Preserved",
            "minecraft:book",
            "Combine paper and leather into books for later progression.",
            10,
            4,
        )
        .depends_on(sugar, leather)
        .item("minecraft:book", 8)
        .finish()
    )

    saplings = (
        survival.quest(
            "tree_farm",
            "Renewable Timber",
            "minecraft:oak_sapling",
            "Plant a dedicated tree farm so construction never depends on distant forests.",
            2,
            7,
        )
        .depends_on(begin)
        .item("minecraft:oak_sapling", 8)
        .finish()
    )
    charcoal = (
        survival.quest(
            "charcoal",
            "Fuel from the Forest",
            "minecraft:charcoal",
            "Smelt logs into charcoal for a renewable source of fuel and torches.",
            4,
            7,
        )
        .depends_on(saplings)
        .item("minecraft:charcoal", 16)
        .finish()
    )
    lanterns = (
        survival.quest(
            "lanterns",
            "Light the Way",
            "minecraft:lantern",
            "Replace temporary darkness with reliable lighting around your base.",
            6,
            7,
        )
        .depends_on(charcoal)
        .item("minecraft:lantern", 8)
        .finish()
    )

    compass = (
        survival.quest(
            "compass",
            "Never Truly Lost",
            "minecraft:compass",
            "Craft a compass before venturing far from your spawn region.",
            8,
            -2,
        )
        .depends_on(ranged, signs)
        .item("minecraft:compass")
        .finish()
    )
    clock = (
        survival.quest(
            "clock",
            "Timekeeper",
            "minecraft:clock",
            "A clock helps track the surface day-night cycle while underground or indoors.",
            10,
            -2,
            optional=True,
        )
        .depends_on(compass)
        .item("minecraft:clock")
        .finish()
    )

    return survival.quest(
        "established",
        "A Proper Homestead",
        "minecraft:golden_carrot",
        (
            "Your base now has storage, defense, renewable food, water, lighting, and "
            "the materials needed for deeper progression."
        ),
        12,
        2,
    ).depends_on(bread, smoker, books, lanterns, compass).checkmark().reward_item(
        "minecraft:golden_carrot", 16
    ).finish()




def _build_mining(project: Project, survival_complete: str) -> None:
    mining = ChapterBuilder(
        project,
        slug="02_mining",
        title="Mining",
        icon="minecraft:diamond_pickaxe",
        description="Descend safely, process valuable ores, and prepare for the Nether.",
    )

    begin = (
        mining.quest(
            "begin",
            "Beneath the Surface",
            "minecraft:stone_pickaxe",
            "Prepare to leave the safety of your homestead and establish a dependable mining operation.",
            0,
            0,
        )
        .depends_on(survival_complete)
        .checkmark()
        .finish()
    )

    iron_pick = (
        mining.quest(
            "iron_pickaxe",
            "The Right Tool",
            "minecraft:iron_pickaxe",
            "Craft an iron pickaxe so valuable ores can be harvested instead of destroyed.",
            2,
            -3,
        )
        .depends_on(begin)
        .item("minecraft:iron_pickaxe")
        .finish()
    )
    torches = (
        mining.quest(
            "torches",
            "Bring More Light",
            "minecraft:torch",
            "Carry a large supply of torches before exploring deep caves and abandoned tunnels.",
            2,
            -1,
        )
        .depends_on(begin)
        .item("minecraft:torch", 64)
        .finish()
    )
    ladders = (
        mining.quest(
            "ladders",
            "A Safe Way Back",
            "minecraft:ladder",
            "Keep ladders available for vertical shafts, ravines, and emergency exits.",
            2,
            1,
            optional=True,
        )
        .depends_on(begin)
        .item("minecraft:ladder", 16)
        .finish()
    )
    bucket = (
        mining.quest(
            "water_bucket",
            "Miner's Best Friend",
            "minecraft:water_bucket",
            "A water bucket can neutralize lava, descend cliffs, and create an emergency escape route.",
            2,
            3,
        )
        .depends_on(begin)
        .item("minecraft:water_bucket")
        .finish()
    )

    coal = (
        mining.quest(
            "coal",
            "Black Gold",
            "minecraft:coal",
            "Gather coal for dependable fuel and underground lighting.",
            4,
            -3,
        )
        .depends_on(iron_pick, torches)
        .item("minecraft:coal", 32)
        .finish()
    )
    raw_iron = (
        mining.quest(
            "raw_iron",
            "Iron Veins",
            "minecraft:raw_iron",
            "Mine a useful stockpile of raw iron for tools, armor, rails, and machines.",
            4,
            -1,
        )
        .depends_on(iron_pick)
        .item("minecraft:raw_iron", 32)
        .finish()
    )
    copper = (
        mining.quest(
            "copper",
            "Conductive Metal",
            "minecraft:raw_copper",
            "Collect copper now; many technology paths will consume it later.",
            4,
            1,
        )
        .depends_on(iron_pick)
        .item("minecraft:raw_copper", 32)
        .finish()
    )
    redstone = (
        mining.quest(
            "redstone",
            "A Spark of Possibility",
            "minecraft:redstone",
            "Mine redstone dust, the foundation of automation and many modded recipes.",
            4,
            3,
        )
        .depends_on(iron_pick, bucket)
        .item("minecraft:redstone", 32)
        .finish()
    )

    blast_furnace = (
        mining.quest(
            "blast_furnace",
            "Faster Smelting",
            "minecraft:blast_furnace",
            "Craft a blast furnace to process ore products more quickly.",
            6,
            -3,
        )
        .depends_on(raw_iron)
        .item("minecraft:blast_furnace")
        .finish()
    )
    iron_stockpile = (
        mining.quest(
            "iron_ingots",
            "Industrial Reserve",
            "minecraft:iron_ingot",
            "Smelt enough iron to support larger projects without immediately returning underground.",
            6,
            -1,
        )
        .depends_on(raw_iron, blast_furnace)
        .item("minecraft:iron_ingot", 64)
        .reward_item("minecraft:rail", 32)
        .finish()
    )
    copper_ingots = (
        mining.quest(
            "copper_ingots",
            "Refined Copper",
            "minecraft:copper_ingot",
            "Process a reserve of copper for building and future technology chapters.",
            6,
            1,
        )
        .depends_on(copper, blast_furnace)
        .item("minecraft:copper_ingot", 32)
        .finish()
    )
    lapis = (
        mining.quest(
            "lapis",
            "Blue Knowledge",
            "minecraft:lapis_lazuli",
            "Collect lapis lazuli for enchanting and decorative blocks.",
            6,
            3,
        )
        .depends_on(redstone)
        .item("minecraft:lapis_lazuli", 24)
        .finish()
    )

    gold = (
        mining.quest(
            "gold",
            "All That Glitters",
            "minecraft:raw_gold",
            "Mine raw gold for powered rails, clocks, golden foods, and advanced crafting.",
            8,
            -3,
        )
        .depends_on(iron_stockpile)
        .item("minecraft:raw_gold", 16)
        .finish()
    )
    deepslate = (
        mining.quest(
            "deepslate",
            "The Deep Dark Stone",
            "minecraft:cobbled_deepslate",
            "Reach the deepslate layers where many valuable ores become more common.",
            8,
            -1,
        )
        .depends_on(iron_stockpile, torches)
        .item("minecraft:cobbled_deepslate", 64)
        .finish()
    )
    rails = (
        mining.quest(
            "rails",
            "Underground Transit",
            "minecraft:rail",
            "Lay the groundwork for transporting yourself and materials through long tunnels.",
            8,
            1,
            optional=True,
        )
        .depends_on(iron_stockpile, redstone)
        .item("minecraft:rail", 64)
        .finish()
    )
    minecart = (
        mining.quest(
            "minecart",
            "Ride the Line",
            "minecraft:minecart",
            "Craft a minecart for moving through your underground network.",
            10,
            1,
            optional=True,
        )
        .depends_on(rails)
        .item("minecraft:minecart")
        .finish()
    )

    diamonds = (
        mining.quest(
            "diamonds",
            "Diamonds!",
            "minecraft:diamond",
            "Find diamonds and enter the next tier of tools, enchanting, and portal construction.",
            10,
            -2,
        )
        .depends_on(deepslate, bucket)
        .advancement("minecraft:story/mine_diamond")
        .reward_item("minecraft:experience_bottle", 8)
        .finish()
    )
    diamond_pick = (
        mining.quest(
            "diamond_pickaxe",
            "A Cut Above",
            "minecraft:diamond_pickaxe",
            "Craft a diamond pickaxe capable of harvesting obsidian.",
            12,
            -3,
        )
        .depends_on(diamonds)
        .item("minecraft:diamond_pickaxe")
        .finish()
    )
    diamond_armor = (
        mining.quest(
            "diamond_armor",
            "Brilliant Protection",
            "minecraft:diamond_chestplate",
            "Begin upgrading your defenses with a diamond chestplate.",
            12,
            -1,
            optional=True,
        )
        .depends_on(diamonds)
        .item("minecraft:diamond_chestplate")
        .finish()
    )
    obsidian = (
        mining.quest(
            "obsidian",
            "Frozen Fire",
            "minecraft:obsidian",
            "Harvest obsidian for enchanting and access to the Nether.",
            14,
            -3,
        )
        .depends_on(diamond_pick, bucket)
        .item("minecraft:obsidian", 14)
        .finish()
    )

    book = (
        mining.quest(
            "book",
            "Written Preparation",
            "minecraft:book",
            "Set aside a book for the enchanting table.",
            10,
            3,
        )
        .depends_on(lapis)
        .item("minecraft:book")
        .finish()
    )
    enchanting = (
        mining.quest(
            "enchanting_table",
            "Power in Words",
            "minecraft:enchanting_table",
            "Craft an enchanting table to improve tools, weapons, and armor.",
            16,
            -1,
        )
        .depends_on(obsidian, book, diamonds)
        .item("minecraft:enchanting_table")
        .finish()
    )
    bookshelves = (
        mining.quest(
            "bookshelves",
            "A Proper Library",
            "minecraft:bookshelf",
            "Gather fifteen bookshelves to unlock the enchanting table's full potential.",
            18,
            -1,
        )
        .depends_on(enchanting)
        .item("minecraft:bookshelf", 15)
        .finish()
    )
    anvil = (
        mining.quest(
            "anvil",
            "Repair and Combine",
            "minecraft:anvil",
            "Craft an anvil for repairing equipment and combining enchanted items.",
            14,
            1,
        )
        .depends_on(iron_stockpile)
        .item("minecraft:anvil")
        .finish()
    )
    grindstone = (
        mining.quest(
            "grindstone",
            "A Fresh Edge",
            "minecraft:grindstone",
            "Use a grindstone to repair tools and remove unwanted enchantments.",
            16,
            1,
            optional=True,
        )
        .depends_on(anvil)
        .item("minecraft:grindstone")
        .finish()
    )

    flint_steel = (
        mining.quest(
            "flint_and_steel",
            "Strike a Spark",
            "minecraft:flint_and_steel",
            "Craft flint and steel so your obsidian frame can become a portal.",
            16,
            -3,
        )
        .depends_on(obsidian)
        .item("minecraft:flint_and_steel")
        .finish()
    )
    golden_apple = (
        mining.quest(
            "golden_apple",
            "Emergency Rations",
            "minecraft:golden_apple",
            "Craft a golden apple before entering more dangerous dimensions and structures.",
            12,
            3,
            optional=True,
        )
        .depends_on(gold)
        .item("minecraft:golden_apple")
        .finish()
    )
    portal = (
        mining.quest(
            "nether_portal",
            "A Doorway of Obsidian",
            "minecraft:flint_and_steel",
            "Construct and ignite a Nether portal. Crossing it will begin the next stage of progression.",
            18,
            -3,
        )
        .depends_on(flint_steel, diamond_armor)
        .advancement("minecraft:story/enter_the_nether")
        .finish()
    )

    return mining.quest(
        "mastery",
        "Master of the Underground",
        "minecraft:diamond",
        (
            "You have established safe mining practices, secured the major overworld ores, "
            "and prepared enchanting and Nether infrastructure."
        ),
        20,
        0,
    ).depends_on(bookshelves, anvil, portal, copper_ingots, lapis).checkmark().reward_item(
        "minecraft:diamond", 3
    ).finish()


def _build_exploration(project: Project, survival_complete: str) -> str:
    exploration = ChapterBuilder(
        project,
        slug="03_exploration",
        title="Exploration",
        icon="minecraft:filled_map",
        description="Chart the overworld, discover distant structures, and return home with rare treasures.",
    )

    begin = exploration.quest(
        "begin", "Beyond the Horizon", "minecraft:filled_map",
        "Your homestead is secure. Pack supplies, choose a direction, and begin charting the wider world.",
        0, 0,
    ).depends_on(survival_complete).checkmark().finish()

    compass = exploration.quest(
        "compass", "Find Your Way Home", "minecraft:compass",
        "Carry a compass so long journeys do not permanently separate you from familiar ground.",
        2, -3,
    ).depends_on(begin).item("minecraft:compass").finish()
    map_item = exploration.quest(
        "map", "Put It on the Map", "minecraft:map",
        "Craft an empty map and begin recording the terrain around your base.",
        4, -3,
    ).depends_on(compass).item("minecraft:map").finish()
    spyglass = exploration.quest(
        "spyglass", "A Distant View", "minecraft:spyglass",
        "Use copper and amethyst to craft a spyglass for scouting terrain and structures from safety.",
        6, -3,
        optional=True,
    ).depends_on(map_item).item("minecraft:spyglass").finish()
    cartography = exploration.quest(
        "cartography_table", "The Cartographer's Desk", "minecraft:cartography_table",
        "Craft a cartography table to copy, expand, and lock maps for a growing expedition archive.",
        6, -1,
    ).depends_on(map_item).item("minecraft:cartography_table").finish()

    boat = exploration.quest(
        "boat", "Take to the Water", "minecraft:oak_boat",
        "Craft a boat before following rivers and coastlines into unexplored territory.",
        2, -1,
    ).depends_on(begin).item("minecraft:oak_boat").finish()
    ocean = exploration.quest(
        "ocean", "Open Water", "minecraft:heart_of_the_sea",
        "Reach an ocean and confirm the discovery after establishing a safe shoreline landing point.",
        4, 1,
    ).depends_on(boat).checkmark().finish()
    shipwreck = exploration.quest(
        "shipwreck", "Wreck Beneath the Waves", "minecraft:chest",
        "Locate and explore a shipwreck. Search every compartment before continuing the expedition.",
        6, 1,
    ).depends_on(ocean).checkmark().finish()
    buried_treasure = exploration.quest(
        "buried_treasure", "X Marks the Spot", "minecraft:heart_of_the_sea",
        "Follow a buried treasure map and recover a Heart of the Sea from the hidden chest.",
        8, 1,
    ).depends_on(shipwreck).item("minecraft:heart_of_the_sea").reward_item("minecraft:emerald", 8).finish()
    ocean_monument = exploration.quest(
        "ocean_monument", "Guardians of the Deep", "minecraft:prismarine_bricks",
        "Discover an ocean monument. Conquering it can wait until you are properly equipped.",
        10, 1,
        optional=True,
    ).depends_on(buried_treasure).checkmark().finish()

    village = exploration.quest(
        "village", "Signs of Civilization", "minecraft:emerald",
        "Find a village and secure it as a useful stop along your travel network.",
        2, 1,
    ).depends_on(begin).checkmark().finish()
    trade = exploration.quest(
        "trade", "A Fair Exchange", "minecraft:emerald",
        "Complete a trade with a villager and begin learning which professions support your progression.",
        4, 3,
    ).depends_on(village).advancement("minecraft:adventure/trade").finish()
    bell = exploration.quest(
        "bell", "Center of Town", "minecraft:bell",
        "Obtain a bell as a trophy or establish one at a settlement of your own.",
        6, 3,
        optional=True,
    ).depends_on(trade).item("minecraft:bell").finish()
    outpost = exploration.quest(
        "pillager_outpost", "Hostile Neighbors", "minecraft:crossbow",
        "Locate a pillager outpost and mark it on your map before deciding whether to attack.",
        6, 5,
    ).depends_on(village).checkmark().finish()
    raid = exploration.quest(
        "raid", "Hero of the Village", "minecraft:totem_of_undying",
        "Defend a village from a raid and earn recognition as its hero.",
        8, 5,
        optional=True,
    ).depends_on(outpost).advancement("minecraft:adventure/hero_of_the_village").finish()

    ruined_portal = exploration.quest(
        "ruined_portal", "Echoes of Another World", "minecraft:crying_obsidian",
        "Find a ruined portal and inspect the remains for clues, obsidian, and useful loot.",
        2, 3,
    ).depends_on(begin).checkmark().finish()
    desert_temple = exploration.quest(
        "desert_temple", "Buried in Sand", "minecraft:chiseled_sandstone",
        "Discover a desert pyramid and carefully disarm the trap beneath its central chamber.",
        4, 5,
    ).depends_on(ruined_portal).checkmark().finish()
    jungle_temple = exploration.quest(
        "jungle_temple", "Secrets in the Vines", "minecraft:mossy_cobblestone",
        "Locate a jungle temple and survive its traps to claim the hidden loot.",
        4, 7,
        optional=True,
    ).depends_on(ruined_portal).checkmark().finish()
    igloo = exploration.quest(
        "igloo", "A Chilling Discovery", "minecraft:snow_block",
        "Find an igloo and investigate whether anything unusual lies beneath it.",
        6, 7,
        optional=True,
    ).depends_on(ruined_portal).checkmark().finish()

    lush_cave = exploration.quest(
        "lush_cave", "A Garden Underground", "minecraft:glow_berries",
        "Explore a lush cave and collect glow berries from its hanging vines.",
        8, -3,
    ).depends_on(spyglass).item("minecraft:glow_berries", 8).finish()
    dripstone = exploration.quest(
        "dripstone_cave", "Stone from Stone", "minecraft:pointed_dripstone",
        "Explore a dripstone cave and gather pointed dripstone for building and renewable lava systems.",
        10, -3,
    ).depends_on(lush_cave).item("minecraft:pointed_dripstone", 16).finish()
    amethyst = exploration.quest(
        "amethyst_geode", "Crystal Resonance", "minecraft:amethyst_shard",
        "Locate an amethyst geode and harvest shards without destroying every budding block.",
        12, -3,
    ).depends_on(dripstone).item("minecraft:amethyst_shard", 16).finish()

    saddle = exploration.quest(
        "saddle", "A Faster Mount", "minecraft:saddle",
        "Recover a saddle from exploration loot and prepare a reliable land mount.",
        8, 3,
    ).depends_on(trade, shipwreck).item("minecraft:saddle").finish()
    lead = exploration.quest(
        "lead", "Traveling Companions", "minecraft:lead",
        "Carry leads for moving animals safely between distant settlements and your home base.",
        10, 3,
        optional=True,
    ).depends_on(saddle).item("minecraft:lead", 2).finish()
    mansion = exploration.quest(
        "woodland_mansion", "Deep Woodland Secrets", "minecraft:dark_oak_log",
        "Locate a woodland mansion. Mark the route and return only when prepared for its defenders.",
        12, 3,
        optional=True,
    ).depends_on(cartography, trade).checkmark().finish()

    adventuring_time = exploration.quest(
        "adventuring_time", "A World of Biomes", "minecraft:grass_block",
        "Continue exploring until you have visited every biome required by the Adventuring Time advancement.",
        12, 0,
        optional=True,
    ).depends_on(amethyst, mansion, ocean_monument).advancement("minecraft:adventure/adventuring_time").finish()

    return exploration.quest(
        "experienced_explorer", "Experienced Explorer", "minecraft:recovery_compass",
        "You have mapped distant lands, traded with settlements, explored natural wonders, and recovered rare treasures.",
        14, 1,
    ).depends_on(buried_treasure, trade, desert_temple, amethyst, saddle).checkmark().reward_item(
        "minecraft:ender_pearl", 8
    ).finish()

def create_project() -> Project:
    project = Project(name="Immersive Adventure Neo", version="13")
    welcome_complete = _build_welcome(project)
    survival_complete = _build_survival(project, welcome_complete)
    mining_complete = _build_mining(project, survival_complete)
    _build_exploration(project, survival_complete)
    create_complete = build_create(project, mining_complete)
    build_actually_additions(project, create_complete)
    return project
