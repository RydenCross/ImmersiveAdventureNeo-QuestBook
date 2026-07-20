from generator.builder import ChapterBuilder


def build_apotheosis_mythic_mastery(chapter: ChapterBuilder, mastery_complete: str) -> str:
    plan = (
        chapter.quest(
            "mythic_mastery_plan",
            "Plan the Mythic Hunt",
            "minecraft:netherite_sword",
            "Choose a specialized endgame build and identify the affixes, gems, sockets, and enchantments needed to complete it.",
            42,
            0,
            optional=True,
        )
        .depends_on(mastery_complete)
        .checkmark()
        .finish()
    )

    boss_route = (
        chapter.quest(
            "boss_hunting_route",
            "Mark the Hunting Grounds",
            "minecraft:compass",
            "Establish a repeatable route for finding dangerous affix enemies and bosses without losing track of safe exits, recovery points, or valuable drops.",
            44,
            4,
            optional=True,
        )
        .depends_on(plan)
        .checkmark()
        .finish()
    )

    trophy_hunt = (
        chapter.quest(
            "mythic_trophy_hunt",
            "Bring Down the Mythic",
            "minecraft:dragon_head",
            "Defeat a top-tier affix enemy or comparable boss and recover a piece of equipment worth evaluating for a permanent build.",
            46,
            4,
            optional=True,
        )
        .depends_on(boss_route)
        .checkmark()
        .reward_item("minecraft:golden_apple", 2)
        .finish()
    )

    salvage_reserve = (
        chapter.quest(
            "salvage_reserve",
            "Salvage at Scale",
            "minecraft:anvil",
            "Build a deep reserve of reforging materials by salvaging advanced equipment that does not fit your intended build.",
            48,
            5,
            optional=True,
        )
        .depends_on(trophy_hunt)
        .checkmark()
        .finish()
    )

    focused_reforge = (
        chapter.quest(
            "focused_reforge",
            "Roll for a Purpose",
            "minecraft:smithing_table",
            "Reforge several candidate items with one clear target in mind, then keep only the result that meaningfully advances the build.",
            50,
            4,
            optional=True,
        )
        .depends_on(salvage_reserve)
        .checkmark()
        .finish()
    )

    gem_sorting = (
        chapter.quest(
            "gem_sorting",
            "Build a Gem Archive",
            "minecraft:amethyst_block",
            "Organize gems by effect, equipment slot, and quality so promising combinations can be compared before they are socketed.",
            44,
            -4,
            optional=True,
        )
        .depends_on(plan)
        .checkmark()
        .finish()
    )

    gem_refinement = (
        chapter.quest(
            "gem_refinement",
            "Refine the Best",
            "minecraft:emerald_block",
            "Upgrade or replace several gems until you have a set of high-quality options suitable for permanent equipment.",
            46,
            -4,
            optional=True,
        )
        .depends_on(gem_sorting)
        .checkmark()
        .finish()
    )

    socket_plan = (
        chapter.quest(
            "socket_plan",
            "Every Socket Has a Job",
            "minecraft:diamond_chestplate",
            "Design a socket plan across your weapon, armor, and tools so each gem supports a specific role instead of duplicating weak effects.",
            48,
            -4,
            optional=True,
        )
        .depends_on(gem_refinement)
        .checkmark()
        .finish()
    )

    socketed_set = (
        chapter.quest(
            "socketed_set",
            "A Fully Socketed Set",
            "minecraft:netherite_chestplate",
            "Complete a coordinated set of socketed equipment with complementary gems across multiple slots.",
            50,
            -3,
            optional=True,
        )
        .depends_on(socket_plan, focused_reforge)
        .checkmark()
        .finish()
    )

    library_wing = (
        chapter.quest(
            "enchanting_library_wing",
            "Expand the Enchanting Archive",
            "minecraft:chiseled_bookshelf",
            "Create a dedicated archive for valuable enchantments, spare books, and planned upgrades so rare effects are never wasted.",
            44,
            0,
            optional=True,
        )
        .depends_on(plan)
        .checkmark()
        .finish()
    )

    shelf_profiles = (
        chapter.quest(
            "shelf_profiles",
            "Build Multiple Shelf Profiles",
            "minecraft:bookshelf",
            "Prepare more than one enchanting setup, each tuned for a different balance of Eterna, Quanta, and Arcana.",
            46,
            0,
            optional=True,
        )
        .depends_on(library_wing)
        .checkmark()
        .finish()
    )

    infusion_workshop = (
        chapter.quest(
            "infusion_workshop",
            "An Infusion Workshop",
            "minecraft:beacon",
            "Build a permanent, documented infusion area with enough space and controlled enchanting statistics for repeated recipes.",
            48,
            0,
            optional=True,
        )
        .depends_on(shelf_profiles)
        .checkmark()
        .finish()
    )

    perfect_enchant = (
        chapter.quest(
            "perfect_enchant",
            "Enchant the Keeper",
            "minecraft:enchanted_book",
            "Apply a carefully planned set of high-value enchantments to an item you intend to preserve for the rest of the playthrough.",
            50,
            0,
            optional=True,
        )
        .depends_on(infusion_workshop, socketed_set)
        .checkmark()
        .finish()
    )

    signature_weapon = (
        chapter.quest(
            "mythic_signature_weapon",
            "Weapon of Legend",
            "minecraft:netherite_sword",
            "Finish a mythic-quality weapon with coherent affixes, sockets, gems, and enchantments built for one combat role.",
            52,
            -2,
            optional=True,
        )
        .depends_on(perfect_enchant)
        .checkmark()
        .finish()
    )

    signature_armor = (
        chapter.quest(
            "mythic_signature_armor",
            "Armor of Legend",
            "minecraft:netherite_chestplate",
            "Finish a coordinated mythic armor set whose affixes, gems, and enchantments reinforce the same defensive or mobility strategy.",
            52,
            2,
            optional=True,
        )
        .depends_on(perfect_enchant)
        .checkmark()
        .finish()
    )

    alternate_loadout = (
        chapter.quest(
            "alternate_loadout",
            "Prepare a Second Build",
            "minecraft:armor_stand",
            "Assemble a second specialized loadout for a different task such as exploration, mining, spellcasting, or boss combat.",
            54,
            0,
            optional=True,
        )
        .depends_on(signature_weapon, signature_armor)
        .checkmark()
        .finish()
    )

    no_death_trial = (
        chapter.quest(
            "no_death_trial",
            "The Unbroken Trial",
            "minecraft:totem_of_undying",
            "Complete a dangerous boss fight or extended expedition with the finished equipment without dying or abandoning the encounter.",
            56,
            -2,
            optional=True,
        )
        .depends_on(alternate_loadout)
        .checkmark()
        .finish()
    )

    gauntlet = (
        chapter.quest(
            "mythic_gauntlet",
            "Run the Mythic Gauntlet",
            "minecraft:wither_skeleton_skull",
            "Defeat several serious threats in succession while relying on your completed loadouts, repair plan, and emergency supplies.",
            56,
            2,
            optional=True,
        )
        .depends_on(alternate_loadout)
        .checkmark()
        .finish()
    )

    museum = (
        chapter.quest(
            "apotheosis_museum",
            "Preserve the Journey",
            "minecraft:armor_stand",
            "Create a display for retired affix gear, exceptional gems, and milestone equipment that records the evolution of your build.",
            58,
            3,
            optional=True,
        )
        .depends_on(gauntlet)
        .checkmark()
        .finish()
    )

    return (
        chapter.quest(
            "mythic_mastery_complete",
            "Beyond Apotheosis",
            "minecraft:netherite_block",
            "You have mastered mythic hunting, gem refinement, specialized reforging, advanced enchanting, multiple equipment builds, and the trials needed to prove them.",
            60,
            0,
            optional=True,
        )
        .depends_on(no_death_trial, gauntlet, museum)
        .checkmark()
        .reward_item("minecraft:netherite_ingot", 2)
        .finish()
    )
