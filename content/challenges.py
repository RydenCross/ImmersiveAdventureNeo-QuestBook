from generator.builder import ChapterBuilder
from model import Project


def build_challenges(project: Project, endgame_complete: str) -> str:
    chapter = ChapterBuilder(
        project,
        slug="11_challenges",
        title="Challenges",
        icon="minecraft:dragon_egg",
        description=(
            "Optional long-term goals for builders, explorers, engineers, mages, "
            "collectors, and completionists who want to push the pack further."
        ),
    )

    begin = (
        chapter.quest(
            "begin",
            "Beyond Completion",
            "minecraft:dragon_egg",
            (
                "The main journey is complete, but mastery has no finish line. Choose any branch "
                "that inspires you; these objectives are optional and designed for long-term worlds."
            ),
            0,
            0,
            optional=True,
        )
        .depends_on(endgame_complete)
        .checkmark()
        .finish()
    )

    # Resource and storage challenges.
    warehouse = (
        chapter.quest(
            "warehouse",
            "The Grand Warehouse",
            "ae2:drive",
            "Build a dedicated warehouse or digital-storage hall with clear organization, access, and expansion space.",
            2,
            -5,
            optional=True,
        )
        .depends_on(begin)
        .checkmark()
        .finish()
    )
    million_items = (
        chapter.quest(
            "million_items",
            "A Million Things",
            "ae2:item_storage_cell_64k",
            "Expand your storage system until it can comfortably hold at least one million total items.",
            4,
            -5,
            optional=True,
        )
        .depends_on(warehouse)
        .checkmark()
        .finish()
    )
    stockpile = (
        chapter.quest(
            "stockpile",
            "Industrial Stockpile",
            "minecraft:iron_block",
            "Maintain deep reserves of common building and engineering materials for large projects.",
            6,
            -5,
            optional=True,
        )
        .depends_on(million_items)
        .item("minecraft:iron_block", 64)
        .item("minecraft:copper_block", 64)
        .item("minecraft:redstone_block", 64)
        .item("minecraft:quartz_block", 64)
        .finish()
    )
    rare_stockpile = (
        chapter.quest(
            "rare_stockpile",
            "Treasury of Rarities",
            "minecraft:netherite_block",
            "Assemble a trophy reserve of the world's rarest vanilla resources.",
            8,
            -5,
            optional=True,
        )
        .depends_on(stockpile)
        .item("minecraft:diamond_block", 16)
        .item("minecraft:emerald_block", 16)
        .item("minecraft:netherite_block", 4)
        .finish()
    )

    # Factory challenges.
    megafactory = (
        chapter.quest(
            "megafactory",
            "The Megafactory",
            "create:mechanical_crafter",
            "Construct a visually coherent factory containing multiple independent production lines and shared logistics.",
            2,
            -2.5,
            optional=True,
        )
        .depends_on(begin)
        .checkmark()
        .finish()
    )
    twenty_autocrafts = (
        chapter.quest(
            "twenty_autocrafts",
            "Catalog of Automation",
            "ae2:pattern_encoding_terminal",
            "Encode and validate at least twenty useful crafting or processing patterns used by your base.",
            4,
            -2.5,
            optional=True,
        )
        .depends_on(megafactory)
        .checkmark()
        .finish()
    )
    continuous_line = (
        chapter.quest(
            "continuous_line",
            "Continuous Production",
            "create:stockpile_switch",
            "Run a demand-controlled production line that automatically starts, stops, and restocks without manual input.",
            6,
            -2.5,
            optional=True,
        )
        .depends_on(twenty_autocrafts)
        .checkmark()
        .finish()
    )
    remote_industry = (
        chapter.quest(
            "remote_industry",
            "Industry without Borders",
            "create:track_station",
            "Operate a remote industrial site connected to your main base by automated freight or networked logistics.",
            8,
            -2.5,
            optional=True,
        )
        .depends_on(continuous_line)
        .checkmark()
        .finish()
    )

    # Power challenges.
    power_station = (
        chapter.quest(
            "power_station",
            "A Monument to Power",
            "mekanism:induction_casing",
            "Build a dedicated, accessible power station with generation, storage, monitoring, and emergency controls.",
            2,
            0,
            optional=True,
        )
        .depends_on(begin)
        .checkmark()
        .finish()
    )
    energy_reserve = (
        chapter.quest(
            "energy_reserve",
            "Deep Energy Reserves",
            "mekanism:ultimate_induction_cell",
            "Expand stored energy until the base can survive an extended generation outage at full operational load.",
            4,
            0,
            optional=True,
        )
        .depends_on(power_station)
        .checkmark()
        .finish()
    )
    reactor_output = (
        chapter.quest(
            "reactor_output",
            "Push the Reactor",
            "mekanismgenerators:fission_reactor_port",
            "Safely raise reactor throughput while maintaining stable coolant, waste, turbine, and shutdown systems.",
            6,
            0,
            optional=True,
        )
        .depends_on(energy_reserve)
        .checkmark()
        .finish()
    )
    black_start = (
        chapter.quest(
            "black_start",
            "Black-Start Test",
            "minecraft:lever",
            "Demonstrate that your grid can recover from a total shutdown using a documented and safe restart procedure.",
            8,
            0,
            optional=True,
        )
        .depends_on(reactor_output)
        .checkmark()
        .finish()
    )

    # Magic and equipment challenges.
    archmage = (
        chapter.quest(
            "archmage",
            "Archmage's Arsenal",
            "ars_nouveau:archmage_spell_book",
            "Create a complete set of polished utility, mobility, combat, building, and emergency spells.",
            2,
            2.5,
            optional=True,
        )
        .depends_on(begin)
        .checkmark()
        .finish()
    )
    ritual_site = (
        chapter.quest(
            "ritual_site",
            "The Grand Ritual Site",
            "ars_nouveau:ritual_brazier",
            "Build a permanent ritual area with source storage, relays, decoration, and safe operating space.",
            4,
            2.5,
            optional=True,
        )
        .depends_on(archmage)
        .checkmark()
        .finish()
    )
    legendary_set = (
        chapter.quest(
            "legendary_set",
            "A Legendary Loadout",
            "minecraft:netherite_chestplate",
            "Assemble a fully enchanted, affixed, socketed, and purpose-built endgame equipment set.",
            6,
            2.5,
            optional=True,
        )
        .depends_on(ritual_site)
        .checkmark()
        .finish()
    )
    no_death_trial = (
        chapter.quest(
            "no_death_trial",
            "Untouchable",
            "minecraft:totem_of_undying",
            "Complete a difficult expedition or boss run without dying or consuming a Totem of Undying.",
            8,
            2.5,
            optional=True,
        )
        .depends_on(legendary_set)
        .checkmark()
        .finish()
    )

    # Exploration and boss challenges.
    world_tour = (
        chapter.quest(
            "world_tour",
            "World Tour",
            "minecraft:filled_map",
            "Visit and document every major biome family and dimension represented in your world.",
            2,
            5,
            optional=True,
        )
        .depends_on(begin)
        .checkmark()
        .finish()
    )
    structure_hunter = (
        chapter.quest(
            "structure_hunter",
            "Structure Hunter",
            "minecraft:recovery_compass",
            "Discover a broad collection of rare structures and preserve trophies or maps from the journey.",
            4,
            5,
            optional=True,
        )
        .depends_on(world_tour)
        .checkmark()
        .finish()
    )
    boss_rush = (
        chapter.quest(
            "boss_rush",
            "Boss Rush",
            "minecraft:wither_skeleton_skull",
            "Defeat the Ender Dragon, Wither, and your pack's major optional bosses during one prepared campaign.",
            6,
            5,
            optional=True,
        )
        .depends_on(structure_hunter)
        .checkmark()
        .finish()
    )
    beacon_monument = (
        chapter.quest(
            "beacon_monument",
            "Light across the World",
            "minecraft:beacon",
            "Construct a full-power beacon monument as a permanent symbol of your completed boss campaign.",
            8,
            5,
            optional=True,
        )
        .depends_on(boss_rush)
        .item("minecraft:beacon")
        .finish()
    )
    dragon_egg = (
        chapter.quest(
            "dragon_egg",
            "A Proper Trophy Room",
            "minecraft:dragon_egg",
            "Build a museum or trophy hall displaying the Dragon Egg, boss drops, rare artifacts, and questbook milestones.",
            10,
            5,
            optional=True,
        )
        .depends_on(beacon_monument)
        .item("minecraft:dragon_egg")
        .item("minecraft:nether_star", 4)
        .finish()
    )

    # Building and community challenges.
    city = (
        chapter.quest(
            "city",
            "A Living City",
            "minecraft:bell",
            "Expand beyond a functional base into a connected settlement with distinct districts and public spaces.",
            10,
            -3.75,
            optional=True,
        )
        .depends_on(remote_industry, rare_stockpile)
        .checkmark()
        .finish()
    )
    transit = (
        chapter.quest(
            "transit",
            "Public Transit",
            "create:track",
            "Create a reliable passenger network connecting your major districts, factories, and exploration hubs.",
            12,
            -3.75,
            optional=True,
        )
        .depends_on(city)
        .checkmark()
        .finish()
    )
    beautification = (
        chapter.quest(
            "beautification",
            "Form and Function",
            "minecraft:flowering_azalea",
            "Landscape and decorate your industrial world so major systems are both readable and beautiful.",
            14,
            -3.75,
            optional=True,
        )
        .depends_on(transit)
        .checkmark()
        .finish()
    )

    # Reliability and completionist challenges.
    uptime = (
        chapter.quest(
            "uptime",
            "Forty-Eight Hours Unattended",
            "minecraft:clock",
            "Keep the main base operating for a long play period without clearing jams, refilling buffers, or resetting machines.",
            10,
            0,
            optional=True,
        )
        .depends_on(black_start, continuous_line)
        .checkmark()
        .finish()
    )
    disaster_drill = (
        chapter.quest(
            "disaster_drill",
            "Disaster Drill",
            "minecraft:redstone_torch",
            "Simulate a controlled failure and prove that alarms, shutdowns, backups, and recovery procedures work as designed.",
            12,
            0,
            optional=True,
        )
        .depends_on(uptime)
        .checkmark()
        .finish()
    )
    knowledge_archive = (
        chapter.quest(
            "knowledge_archive",
            "The Knowledge Archive",
            "minecraft:bookshelf",
            "Document important systems, recipes, coordinates, operating procedures, and future plans inside the world.",
            10,
            3.75,
            optional=True,
        )
        .depends_on(no_death_trial, dragon_egg)
        .checkmark()
        .finish()
    )
    every_branch = (
        chapter.quest(
            "every_branch",
            "Master of Every Discipline",
            "minecraft:enchanted_golden_apple",
            "Complete every major branch of this Challenges chapter.",
            14,
            1.5,
            optional=True,
        )
        .depends_on(beautification, disaster_drill, knowledge_archive)
        .checkmark()
        .reward_item("minecraft:enchanted_golden_apple")
        .finish()
    )

    return (
        chapter.quest(
            "completionist",
            "The Immersive Completionist",
            "minecraft:nether_star",
            (
                "You did more than finish the pack: you transformed its systems into a persistent, "
                "beautiful, documented, and resilient world. This is the final optional accolade."
            ),
            16,
            1.5,
            optional=True,
        )
        .depends_on(every_branch)
        .checkmark()
        .reward_item("minecraft:nether_star", 8)
        .finish()
    )
