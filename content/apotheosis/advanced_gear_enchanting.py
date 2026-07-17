from generator.builder import ChapterBuilder


def build_apotheosis_advanced_gear_enchanting(
    chapter: ChapterBuilder, foundations_complete: str
) -> str:

    hunt = (
        chapter.quest(
            "advanced_hunt",
            "Hunt for Greater Power",
            "minecraft:netherite_sword",
            (
                "Seek stronger affix enemies and higher-rarity equipment. Advanced Apotheosis "
                "progression begins when you can reliably replace merely useful gear with items "
                "that support a deliberate endgame build."
            ),
            22,
            0,
        )
        .depends_on(foundations_complete)
        .checkmark()
        .finish()
    )

    rarity = (
        chapter.quest(
            "higher_rarity",
            "Climb the Rarity Ladder",
            "minecraft:netherite_chestplate",
            (
                "Obtain a piece of equipment from a higher rarity tier than your current loadout. "
                "Compare its affix count and quality rather than assuming rarity alone makes it best."
            ),
            24,
            -2,
        )
        .depends_on(hunt)
        .checkmark()
        .finish()
    )

    boss = (
        chapter.quest(
            "advanced_affix_enemy",
            "Face an Empowered Foe",
            "minecraft:dragon_head",
            (
                "Defeat a dangerous affix-bearing enemy, boss, or similarly empowered target. "
                "These encounters are the most direct source of exceptional gear and gems."
            ),
            24,
            2,
        )
        .depends_on(hunt)
        .checkmark()
        .reward_item("minecraft:golden_apple", 2)
        .finish()
    )

    materials = (
        chapter.quest(
            "reforging_materials",
            "Better Materials, Better Possibilities",
            "minecraft:netherite_scrap",
            (
                "Build a reserve of higher-tier reforging materials by salvaging unwanted advanced "
                "equipment. Better materials open access to stronger rarity and affix outcomes."
            ),
            26,
            2,
        )
        .depends_on(boss)
        .checkmark()
        .finish()
    )

    reforge = (
        chapter.quest(
            "advanced_reforge",
            "Reforge with Intent",
            "minecraft:anvil",
            (
                "Reforge a favored item using improved materials. Set a goal before rolling: damage, "
                "defense, mobility, mining, spell support, or another clear purpose."
            ),
            28,
            0,
        )
        .depends_on(rarity, materials)
        .checkmark()
        .finish()
    )

    affix_set = (
        chapter.quest(
            "coherent_affixes",
            "Affixes That Work Together",
            "minecraft:netherite_helmet",
            (
                "Assemble multiple equipped items whose affixes reinforce the same playstyle. "
                "Synergy across several slots is stronger than one spectacular isolated roll."
            ),
            30,
            0,
        )
        .depends_on(reforge)
        .checkmark()
        .finish()
    )

    gems = (
        chapter.quest(
            "advanced_gems",
            "Gems Worth Keeping",
            "minecraft:emerald",
            (
                "Collect several gems that fit your chosen build and identify which qualities are "
                "worth preserving for permanent equipment."
            ),
            26,
            -3,
        )
        .depends_on(rarity)
        .checkmark()
        .finish()
    )

    upgrade_gem = (
        chapter.quest(
            "upgrade_gem",
            "Refine the Gem",
            "minecraft:amethyst_block",
            (
                "Use Apotheosis gem progression to improve a gem or obtain a meaningfully higher-quality "
                "version of one you already use. Reserve the best results for long-term gear."
            ),
            28,
            -3,
        )
        .depends_on(gems)
        .checkmark()
        .finish()
    )

    sockets = (
        chapter.quest(
            "multiple_sockets",
            "Build Around the Sockets",
            "minecraft:smithing_table",
            (
                "Prepare an item with multiple useful sockets or assemble several socketed equipment "
                "pieces. Plan the socket layout before committing rare gems."
            ),
            30,
            -3,
        )
        .depends_on(upgrade_gem, affix_set)
        .checkmark()
        .finish()
    )

    socket_loadout = (
        chapter.quest(
            "optimized_sockets",
            "A Socketed Loadout",
            "minecraft:diamond",
            (
                "Install complementary gems across your equipment. Avoid duplicate effects that provide "
                "poor returns and make each socket contribute to the build's purpose."
            ),
            32,
            -2,
        )
        .depends_on(sockets)
        .checkmark()
        .finish()
    )

    library = (
        chapter.quest(
            "enchanting_library",
            "A Library of Possibilities",
            "minecraft:chiseled_bookshelf",
            (
                "Create or use Apotheosis enchanting-library storage to collect enchantments for later "
                "application. Centralized storage turns random books into a planned upgrade resource."
            ),
            26,
            4,
        )
        .depends_on(foundations_complete)
        .checkmark()
        .finish()
    )

    extract = (
        chapter.quest(
            "extract_enchantments",
            "Preserve the Best Enchantments",
            "minecraft:enchanted_book",
            (
                "Recover or store a valuable enchantment from equipment or books. Keep rare enchantments "
                "available until the correct permanent item is ready."
            ),
            28,
            4,
        )
        .depends_on(library)
        .checkmark()
        .finish()
    )

    specialized_setup = (
        chapter.quest(
            "specialized_enchanting",
            "Tune the Enchanting Room",
            "minecraft:enchanting_table",
            (
                "Build a specialized shelf arrangement for a specific enchanting goal. Balance Eterna, "
                "Quanta, and Arcana deliberately instead of maximizing every statistic at once."
            ),
            30,
            4,
        )
        .depends_on(extract)
        .checkmark()
        .finish()
    )

    infusion = (
        chapter.quest(
            "infusion",
            "Infuse Beyond Ordinary Crafting",
            "minecraft:beacon",
            (
                "Complete an Apotheosis infusion recipe. Infusion uses carefully controlled enchanting "
                "statistics to create items that ordinary crafting cannot produce."
            ),
            32,
            4,
        )
        .depends_on(specialized_setup)
        .checkmark()
        .finish()
    )

    advanced_enchant = (
        chapter.quest(
            "optimized_enchanting",
            "Enchant with a Plan",
            "minecraft:enchanted_book",
            (
                "Produce a high-value enchantment using a setup tuned for its intended outcome. Record "
                "the shelf balance so the result can be reproduced later."
            ),
            34,
            3,
        )
        .depends_on(infusion)
        .checkmark()
        .reward_item("minecraft:experience_bottle", 16)
        .finish()
    )

    augment = (
        chapter.quest(
            "augment_existing_gear",
            "Improve Without Replacing",
            "minecraft:grindstone",
            (
                "Upgrade an existing keeper item through reforging, sockets, gems, or enchantments rather "
                "than discarding it. Endgame progression is often refinement, not replacement."
            ),
            34,
            0,
        )
        .depends_on(socket_loadout, advanced_enchant)
        .checkmark()
        .finish()
    )

    weapon = (
        chapter.quest(
            "signature_weapon",
            "Forge a Signature Weapon",
            "minecraft:netherite_sword",
            (
                "Complete a weapon whose affixes, gems, and enchantments all support the same combat role. "
                "It should be an item you would repair and preserve rather than casually replace."
            ),
            36,
            -1,
        )
        .depends_on(augment)
        .checkmark()
        .finish()
    )

    armor = (
        chapter.quest(
            "signature_armor",
            "Armor with a Purpose",
            "minecraft:netherite_chestplate",
            (
                "Complete a coordinated armor set or several major armor pieces designed around one goal: "
                "survival, speed, magic, exploration, or another clear specialty."
            ),
            36,
            1,
        )
        .depends_on(augment)
        .checkmark()
        .finish()
    )

    trial = (
        chapter.quest(
            "field_trial",
            "Prove the Build",
            "minecraft:totem_of_undying",
            (
                "Test your completed equipment against a serious threat or demanding expedition. Confirm "
                "that the build performs as intended and identify any weak slot that still needs work."
            ),
            38,
            0,
        )
        .depends_on(weapon, armor)
        .checkmark()
        .finish()
    )

    return (
        chapter.quest(
            "mastery_complete",
            "Apotheosis Mastery",
            "minecraft:netherite_block",
            (
                "You can hunt advanced affix gear, salvage and reforge efficiently, improve gems, plan "
                "socket layouts, tune enchanting statistics, perform infusion, and maintain a coherent "
                "endgame equipment set."
            ),
            40,
            0,
        )
        .depends_on(trial)
        .checkmark()
        .reward_item("minecraft:netherite_ingot")
        .finish()
    )
