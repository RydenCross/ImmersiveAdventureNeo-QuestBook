from generator.builder import ChapterBuilder


def build_ars_nouveau_spellcraft_equipment(
    chapter: ChapterBuilder, foundations_complete: str
) -> str:
    apprentice_book = (
        chapter.quest(
            "apprentice_spell_book",
            "Advance Your Studies",
            "ars_nouveau:apprentice_spell_book",
            "Upgrade to an Apprentice Spell Book. The second tier opens stronger glyphs, more complex spell recipes, and greater room for augments.",
            20,
            -2,
        )
        .depends_on(foundations_complete)
        .item("ars_nouveau:apprentice_spell_book")
        .finish()
    )

    mana_regen = (
        chapter.quest(
            "mana_regeneration",
            "Recover Between Casts",
            "ars_nouveau:mana_regen_ring",
            "Improve your mana regeneration with enchanted equipment, curios, or spellcasting gear. Sustainable magic matters more than one spectacular cast.",
            22,
            -4,
        )
        .depends_on(apprentice_book)
        .checkmark()
        .finish()
    )

    mana_capacity = (
        chapter.quest(
            "mana_capacity",
            "A Deeper Mana Pool",
            "ars_nouveau:mana_boost_ring",
            "Increase your maximum mana so larger spell recipes can be cast reliably. Capacity and regeneration should be developed together.",
            22,
            -2,
        )
        .depends_on(apprentice_book)
        .checkmark()
        .finish()
    )

    augment = (
        chapter.quest(
            "spell_augments",
            "Modify the Formula",
            "ars_nouveau:glyph_amplify",
            "Learn an augment such as Amplify, Extend Time, or AOE. Augments alter an effect without changing the spell's core purpose.",
            22,
            0,
        )
        .depends_on(apprentice_book)
        .checkmark()
        .finish()
    )

    utility_spell = (
        chapter.quest(
            "utility_spell",
            "Magic for Everyday Work",
            "ars_nouveau:glyph_light",
            "Create a utility spell for movement, lighting, harvesting, building, or mining. A good mage solves routine problems without reaching for a tool.",
            24,
            1,
        )
        .depends_on(augment)
        .checkmark()
        .reward_item("minecraft:lapis_lazuli", 8)
        .finish()
    )

    combat_spell = (
        chapter.quest(
            "combat_spell",
            "Shape a Battle Spell",
            "ars_nouveau:glyph_harm",
            "Compose a combat spell with a delivery form, a damaging or controlling effect, and at least one useful augment. Test its mana cost before battle.",
            24,
            -1,
        )
        .depends_on(augment, mana_capacity)
        .checkmark()
        .finish()
    )

    mobility_spell = (
        chapter.quest(
            "mobility_spell",
            "Move Like a Mage",
            "ars_nouveau:glyph_leap",
            "Build a mobility spell using effects such as Launch, Leap, Slowfall, or Blink. Keep a safe version ready for exploration and emergency escapes.",
            24,
            -3,
        )
        .depends_on(augment, mana_regen)
        .checkmark()
        .finish()
    )

    arcanist_armor = (
        chapter.quest(
            "arcanist_armor",
            "Robes of the Arcanist",
            "ars_nouveau:arcanist_robes",
            "Craft a full set of Arcanist armor. Enchant and specialize it to support the spell style you use most often.",
            26,
            -4,
        )
        .depends_on(mana_regen, mana_capacity)
        .item("ars_nouveau:arcanist_robes")
        .item("ars_nouveau:arcanist_leggings")
        .item("ars_nouveau:arcanist_boots")
        .item("ars_nouveau:arcanist_hood")
        .finish()
    )

    threads = (
        chapter.quest(
            "armor_threads",
            "Threaded Enchantments",
            "ars_nouveau:thread_spellpower",
            "Apply a magical thread to mage armor. Threads provide focused bonuses and let your equipment reinforce a chosen magical role.",
            28,
            -4,
        )
        .depends_on(arcanist_armor)
        .checkmark()
        .finish()
    )

    (
        chapter.quest(
            "first_familiar",
            "A Magical Companion",
            "ars_nouveau:familiar_amethyst_golem",
            "Bind a familiar through a suitable ritual. Familiars provide passive benefits and reward mages who build around a particular style.",
            28,
            2,
            optional=True,
        )
        .depends_on(utility_spell)
        .checkmark()
        .finish()
    )

    ritual_brazier = (
        chapter.quest(
            "ritual_brazier",
            "Prepare the Ritual",
            "ars_nouveau:ritual_brazier",
            "Craft a Ritual Brazier and learn how ritual tablets consume Source to perform large-scale magical operations.",
            26,
            3,
        )
        .depends_on(utility_spell)
        .item("ars_nouveau:ritual_brazier")
        .finish()
    )

    first_ritual = (
        chapter.quest(
            "first_ritual",
            "Magic Beyond a Single Cast",
            "ars_nouveau:ritual_flight",
            "Complete a useful ritual for farming, weather control, movement, summoning, or area utility. Plan its Source supply before activation.",
            28,
            3,
        )
        .depends_on(ritual_brazier)
        .checkmark()
        .finish()
    )

    warp_scroll = (
        chapter.quest(
            "warp_scroll",
            "Write a Destination",
            "ars_nouveau:warp_scroll",
            "Create and bind a Warp Scroll. Location-bound magic supports transport, recall spells, and automation across a growing base.",
            26,
            1,
        )
        .depends_on(utility_spell)
        .item("ars_nouveau:warp_scroll")
        .finish()
    )

    relay_warp = (
        chapter.quest(
            "relay_warp",
            "Source Across Distance",
            "ars_nouveau:relay_warp",
            "Craft a Warp Source Relay to move Source across long distances. Use it to connect remote magical systems without a chain of ordinary relays.",
            28,
            0,
        )
        .depends_on(warp_scroll)
        .item("ars_nouveau:relay_warp")
        .finish()
    )

    enchanters_sword = (
        chapter.quest(
            "enchanters_sword",
            "A Weapon That Casts",
            "ars_nouveau:enchanters_sword",
            "Craft an Enchanter's Sword and configure its spell. Spell-linked equipment can combine conventional combat with programmable magic.",
            28,
            -1,
            optional=True,
        )
        .depends_on(combat_spell)
        .item("ars_nouveau:enchanters_sword")
        .finish()
    )

    (
        chapter.quest(
            "enchanters_bow",
            "Arcane Archery",
            "ars_nouveau:enchanters_bow",
            "Craft an Enchanter's Bow and attach a suitable spell. Choose effects that complement ranged combat rather than wasting mana on every shot.",
            30,
            -1,
            optional=True,
        )
        .depends_on(enchanters_sword)
        .item("ars_nouveau:enchanters_bow")
        .finish()
    )

    (
        chapter.quest(
            "advanced_spell_turret",
            "A Smarter Spell Turret",
            "ars_nouveau:spell_turret",
            "Upgrade to an advanced Spell Turret and automate a practical spell. Use filters, redstone, and safe targeting to avoid magical accidents.",
            30,
            2,
            optional=True,
        )
        .depends_on(first_ritual, relay_warp)
        .item("ars_nouveau:spell_turret")
        .finish()
    )

    archmage_book = (
        chapter.quest(
            "archmage_spell_book",
            "The Archmage's Grimoire",
            "ars_nouveau:archmage_spell_book",
            "Upgrade to an Archmage Spell Book. The highest spellbook tier supports the most demanding glyphs and advanced spell recipes.",
            30,
            -3,
        )
        .depends_on(combat_spell, mobility_spell, threads)
        .item("ars_nouveau:archmage_spell_book")
        .finish()
    )

    signature_spell = (
        chapter.quest(
            "signature_spell",
            "Write Your Signature Spell",
            "ars_nouveau:archmage_spell_book",
            "Design a polished high-tier spell with a clear purpose, sensible mana cost, and enough augments to distinguish it from your early experiments.",
            32,
            -2,
        )
        .depends_on(archmage_book)
        .checkmark()
        .reward_item("ars_nouveau:source_gem", 12)
        .finish()
    )

    return (
        chapter.quest(
            "spellcraft_complete",
            "Master of Practical Spellcraft",
            "ars_nouveau:archmage_spell_book",
            "You can build advanced spells, sustain your mana, specialize magical equipment, perform rituals, and extend Source networks across distance.",
            34,
            0,
        )
        .depends_on(signature_spell, first_ritual, relay_warp, threads)
        .checkmark()
        .reward_item("ars_nouveau:source_gem", 16)
        .finish()
    )
