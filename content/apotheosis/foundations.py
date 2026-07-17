from generator.builder import ChapterBuilder
from model import Project


def build_apotheosis_foundations(project: Project, ars_complete: str) -> str:
    chapter = ChapterBuilder(
        project,
        slug="07_apotheosis",
        title="Apotheosis",
        icon="minecraft:anvil",
        description=(
            "Learn affix equipment, rarity, salvaging, reforging, gems, sockets, "
            "and the foundations of advanced enchanting."
        ),
    )

    begin = (
        chapter.quest(
            "begin",
            "Power Hidden in Equipment",
            "minecraft:diamond_sword",
            (
                "Apotheosis turns ordinary equipment into a progression system of affixes, "
                "rarities, gems, sockets, and specialized enchanting. Begin by examining the "
                "unusual gear dropped by dangerous enemies."
            ),
            0,
            0,
        )
        .depends_on(ars_complete)
        .checkmark()
        .finish()
    )

    affix_item = (
        chapter.quest(
            "first_affix_item",
            "More Than a Name",
            "minecraft:iron_sword",
            (
                "Obtain a piece of affix equipment and inspect its tooltip. Affixes can alter "
                "damage, defenses, movement, utility, and many other attributes."
            ),
            2,
            -2,
        )
        .depends_on(begin)
        .checkmark()
        .finish()
    )

    rarity = (
        chapter.quest(
            "rarity_tiers",
            "Colors of Power",
            "minecraft:golden_chestplate",
            (
                "Compare equipment from at least two rarity tiers. Higher rarity usually allows "
                "more or stronger affixes, but the right combination matters more than color alone."
            ),
            4,
            -2,
        )
        .depends_on(affix_item)
        .checkmark()
        .finish()
    )

    bosses = (
        chapter.quest(
            "affix_enemy",
            "A Worthy Opponent",
            "minecraft:wither_skeleton_skull",
            (
                "Defeat an affix-bearing enemy or other elite threat. These encounters are a major "
                "source of randomized equipment and materials for later gear improvement."
            ),
            2,
            1,
        )
        .depends_on(begin)
        .checkmark()
        .reward_item("minecraft:golden_apple")
        .finish()
    )

    compare = (
        chapter.quest(
            "compare_gear",
            "Read Before Replacing",
            "minecraft:spyglass",
            (
                "Compare two similar affix items before choosing one. Evaluate useful attributes, "
                "durability, enchantability, sockets, and how each item supports your build."
            ),
            6,
            -2,
        )
        .depends_on(rarity, bosses)
        .checkmark()
        .finish()
    )

    salvage = (
        chapter.quest(
            "salvaging",
            "Nothing Powerful Goes to Waste",
            "minecraft:grindstone",
            (
                "Use Apotheosis salvaging to break down unwanted affix equipment. Salvaging turns "
                "bad rolls into materials that can fund better equipment later."
            ),
            4,
            1,
        )
        .depends_on(bosses)
        .checkmark()
        .finish()
    )

    salvage_stock = (
        chapter.quest(
            "salvage_stockpile",
            "Build a Material Reserve",
            "minecraft:chest",
            (
                "Salvage several unwanted items and store the results together. A dedicated reserve "
                "makes repeated reforging much easier to manage."
            ),
            6,
            1,
        )
        .depends_on(salvage)
        .checkmark()
        .finish()
    )

    reforging = (
        chapter.quest(
            "reforging",
            "Rewrite the Affixes",
            "minecraft:anvil",
            (
                "Use a reforging station to reroll a piece of affix equipment. Reforging is how you "
                "convert salvaged materials into deliberate upgrades instead of relying only on drops."
            ),
            8,
            0,
        )
        .depends_on(compare, salvage_stock)
        .checkmark()
        .finish()
    )

    keeper = (
        chapter.quest(
            "first_keeper",
            "A Roll Worth Keeping",
            "minecraft:diamond_chestplate",
            (
                "Produce or find an affix item worth keeping for regular use. Favor a coherent set of "
                "bonuses over a collection of impressive but unrelated numbers."
            ),
            10,
            0,
        )
        .depends_on(reforging)
        .checkmark()
        .finish()
    )

    first_gem = (
        chapter.quest(
            "first_gem",
            "Power in a Small Package",
            "minecraft:emerald",
            (
                "Obtain an Apotheosis gem and read its effect. Gems provide targeted bonuses when "
                "inserted into compatible sockets."
            ),
            8,
            3,
        )
        .depends_on(bosses)
        .checkmark()
        .finish()
    )

    gem_quality = (
        chapter.quest(
            "gem_quality",
            "Cut Above the Rest",
            "minecraft:amethyst_shard",
            (
                "Compare gems of different qualities. Save rare gems for equipment you expect to keep, "
                "and use common gems to experiment with socket combinations."
            ),
            10,
            3,
        )
        .depends_on(first_gem)
        .checkmark()
        .finish()
    )

    socket = (
        chapter.quest(
            "socketed_item",
            "An Empty Socket",
            "minecraft:netherite_upgrade_smithing_template",
            (
                "Acquire a socketed item or add a socket through Apotheosis progression. A socket is an "
                "upgrade slot, not an upgrade by itself."
            ),
            12,
            2,
        )
        .depends_on(keeper, gem_quality)
        .checkmark()
        .finish()
    )

    socket_gem = (
        chapter.quest(
            "socket_gem",
            "Set the Gem",
            "minecraft:smithing_table",
            (
                "Insert a useful gem into a socketed item. Match the gem's effect to the equipment slot "
                "and the role that item serves."
            ),
            14,
            2,
        )
        .depends_on(socket)
        .checkmark()
        .finish()
    )

    extraction = (
        chapter.quest(
            "gem_extraction",
            "Plan for Replacement",
            "minecraft:glass_bottle",
            (
                "Learn how gem removal or recovery works before socketing your rarest finds. Some "
                "methods preserve the gem, some preserve the item, and some may require a sacrifice."
            ),
            16,
            2,
            optional=True,
        )
        .depends_on(socket_gem)
        .checkmark()
        .finish()
    )

    enchanting_table = (
        chapter.quest(
            "enchanting_table",
            "Return to the Enchanting Table",
            "minecraft:enchanting_table",
            (
                "Build an enchanting table and prepare a proper enchanting area. Apotheosis expands the "
                "system far beyond the vanilla fifteen-bookshelf setup."
            ),
            8,
            -4,
        )
        .depends_on(rarity)
        .item("minecraft:enchanting_table")
        .finish()
    )

    bookshelves = (
        chapter.quest(
            "bookshelf_stats",
            "More Than Eterna",
            "minecraft:bookshelf",
            (
                "Inspect the enchanting statistics supplied by nearby shelves. Learn the roles of Eterna, "
                "Quanta, and Arcana before expanding the setup blindly."
            ),
            10,
            -4,
        )
        .depends_on(enchanting_table)
        .item("minecraft:bookshelf", 15)
        .finish()
    )

    eterna = (
        chapter.quest(
            "eterna",
            "Raise the Ceiling",
            "minecraft:experience_bottle",
            (
                "Increase Eterna to unlock stronger enchantment levels. Eterna controls the basic power "
                "available to the enchanting table."
            ),
            12,
            -5,
        )
        .depends_on(bookshelves)
        .checkmark()
        .finish()
    )

    quanta = (
        chapter.quest(
            "quanta",
            "Embrace Controlled Chaos",
            "minecraft:chorus_fruit",
            (
                "Experiment with Quanta and observe how it changes enchanting variance. More Quanta can "
                "produce dramatic results, but it also makes outcomes less predictable."
            ),
            12,
            -3,
        )
        .depends_on(bookshelves)
        .checkmark()
        .finish()
    )

    arcana = (
        chapter.quest(
            "arcana",
            "Favor Better Enchantments",
            "minecraft:lapis_lazuli",
            (
                "Increase Arcana and compare the available enchantments. Arcana improves the quality and "
                "rarity of results rather than simply raising their level."
            ),
            14,
            -4,
        )
        .depends_on(eterna, quanta)
        .item("minecraft:lapis_lazuli", 32)
        .finish()
    )

    first_advanced_enchant = (
        chapter.quest(
            "advanced_enchant",
            "Beyond Vanilla Limits",
            "minecraft:enchanted_book",
            (
                "Complete an enchantment using your Apotheosis-enhanced setup. Record the shelf balance "
                "that produced a result you would willingly use."
            ),
            16,
            -4,
        )
        .depends_on(arcana)
        .checkmark()
        .reward_item("minecraft:experience_bottle", 8)
        .finish()
    )

    build = (
        chapter.quest(
            "coherent_build",
            "Build Around a Purpose",
            "minecraft:netherite_sword",
            (
                "Assemble a small equipment loadout whose affixes, gems, and enchantments support one "
                "clear purpose such as mining, exploration, spellcasting, defense, or melee combat."
            ),
            18,
            0,
        )
        .depends_on(socket_gem, first_advanced_enchant, keeper)
        .checkmark()
        .finish()
    )

    return (
        chapter.quest(
            "foundations_complete",
            "The First Apotheosis",
            "minecraft:netherite_chestplate",
            (
                "You can evaluate affix gear, salvage failures, reforge upgrades, socket gems, and tune an "
                "advanced enchanting setup. You are ready for deeper Apotheosis progression."
            ),
            20,
            0,
        )
        .depends_on(build, extraction)
        .checkmark()
        .reward_item("minecraft:diamond", 4)
        .finish()
    )
