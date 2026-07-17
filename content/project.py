from generator.builder import ChapterBuilder
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


def _build_survival(project: Project, welcome_complete: str) -> None:
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

    survival.quest(
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


def create_project() -> Project:
    project = Project(name="Immersive Adventure Neo", version="13")
    welcome_complete = _build_welcome(project)
    _build_survival(project, welcome_complete)
    return project
