from generator.builder import ChapterBuilder
from model import Project


def create_project() -> Project:
    project = Project(name="Immersive Adventure Neo", version="13")
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
            (
                "Collect logs to begin crafting tools and building shelter. "
                "Any common oak log will complete this introductory step."
            ),
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
            "Upgrade to a stone pickaxe. This opens the path to early mining and better resources.",
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

    (
        welcome.quest(
            "ready",
            "Adventure Awaits",
            "minecraft:compass",
            (
                "You understand the basics. Continue into Survival, Mining, and "
                "Exploration as those chapters become available."
            ),
            10,
            0,
        )
        .depends_on(iron)
        .checkmark()
        .reward_item("minecraft:golden_apple")
        .finish()
    )
    return project
