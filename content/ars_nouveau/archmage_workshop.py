from generator.builder import ChapterBuilder


def build_ars_nouveau_archmage_workshop(chapter: ChapterBuilder, spellcraft_complete: str) -> str:
    plan = (
        chapter.quest(
            "archmage_workshop_plan",
            "Plan the Archmage's Workshop",
            "ars_nouveau:archmage_spell_book",
            "Expand your magical workshop into a reliable system for Source generation, ritual work, transport, defense, and automated spellcasting.",
            36,
            0,
            optional=True,
        )
        .depends_on(spellcraft_complete)
        .checkmark()
        .finish()
    )

    source_array = (
        chapter.quest(
            "source_generation_array",
            "A Source for Every Situation",
            "ars_nouveau:source_jar",
            "Operate multiple Sourcelink types so the workshop can generate Source from more than one activity. Diverse generation keeps magic flowing when one process stops.",
            38,
            2,
            optional=True,
        )
        .depends_on(plan)
        .checkmark()
        .finish()
    )

    jar_bank = (
        chapter.quest(
            "source_jar_bank",
            "Build a Source Reservoir",
            "ars_nouveau:source_jar",
            "Create a bank of Source Jars large enough to buffer rituals, apparatus crafting, and spell-turret use without draining the workshop dry.",
            40,
            2,
            optional=True,
        )
        .depends_on(source_array)
        .item("ars_nouveau:source_jar", 8)
        .finish()
    )

    relay_network = (
        chapter.quest(
            "managed_relay_network",
            "Route Source with Purpose",
            "ars_nouveau:relay",
            "Organize Source Relays into clear generation, storage, and consumption routes. Avoid a tangled network that is difficult to diagnose or expand.",
            42,
            2,
            optional=True,
        )
        .depends_on(jar_bank)
        .checkmark()
        .finish()
    )

    remote_source = (
        chapter.quest(
            "remote_source_outpost",
            "Power a Remote Magical Outpost",
            "ars_nouveau:relay_warp",
            "Use Warp Source Relays to supply a distant ritual site, farm, or defensive installation from your central Source network.",
            44,
            3,
            optional=True,
        )
        .depends_on(relay_network)
        .checkmark()
        .finish()
    )

    ritual_library = (
        chapter.quest(
            "ritual_library",
            "A Library of Rituals",
            "ars_nouveau:ritual_brazier",
            "Collect and organize several useful ritual tablets. Keep notes on their Source costs, area of effect, and safe operating conditions.",
            38,
            -2,
            optional=True,
        )
        .depends_on(plan)
        .checkmark()
        .finish()
    )

    sustained_ritual = (
        chapter.quest(
            "sustained_ritual",
            "Sustain a Working Ritual Site",
            "ars_nouveau:ritual_brazier",
            "Build a permanent ritual area with dedicated Source storage and enough clearance for repeated operation.",
            40,
            -2,
            optional=True,
        )
        .depends_on(ritual_library, jar_bank)
        .checkmark()
        .finish()
    )

    transport_network = (
        chapter.quest(
            "magical_transport_network",
            "Travel by Written Destination",
            "ars_nouveau:warp_scroll",
            "Establish a practical magical transport network using bound Warp Scrolls, portals, or teleportation spells between important locations.",
            42,
            -3,
            optional=True,
        )
        .depends_on(sustained_ritual)
        .checkmark()
        .finish()
    )

    familiar_specialization = (
        chapter.quest(
            "familiar_specialization",
            "Choose a Familiar's Calling",
            "ars_nouveau:familiar_amethyst_golem",
            "Bind and use a familiar whose passive benefit supports your preferred style of spellcasting, automation, exploration, or combat.",
            38,
            -5,
            optional=True,
        )
        .depends_on(plan)
        .checkmark()
        .finish()
    )

    familiar_field_test = (
        chapter.quest(
            "familiar_field_test",
            "Work Beside Your Familiar",
            "ars_nouveau:familiar_amethyst_golem",
            "Complete a meaningful expedition or workshop task while actively benefiting from your familiar's specialization.",
            40,
            -5,
            optional=True,
        )
        .depends_on(familiar_specialization)
        .checkmark()
        .finish()
    )

    turret_cell = (
        chapter.quest(
            "turret_cell",
            "Program a Reliable Spell Turret",
            "ars_nouveau:spell_turret",
            "Configure an advanced Spell Turret with a safe, repeatable utility or production spell and a dependable redstone trigger.",
            38,
            5,
            optional=True,
        )
        .depends_on(plan)
        .item("ars_nouveau:spell_turret")
        .finish()
    )

    turret_network = (
        chapter.quest(
            "turret_network",
            "A Network of Automated Magic",
            "ars_nouveau:spell_turret",
            "Operate multiple spell turrets with distinct jobs, such as harvesting, lighting, defense, movement, or block manipulation.",
            40,
            5,
            optional=True,
        )
        .depends_on(turret_cell, relay_network)
        .checkmark()
        .finish()
    )

    safe_targeting = (
        chapter.quest(
            "safe_turret_targeting",
            "Magic with Safeguards",
            "ars_nouveau:spell_turret",
            "Add filters, barriers, redstone interlocks, or controlled targeting so automated spells cannot harm allies or damage the workshop.",
            42,
            5,
            optional=True,
        )
        .depends_on(turret_network)
        .checkmark()
        .finish()
    )

    apparatus_automation = (
        chapter.quest(
            "apparatus_automation",
            "Automate the Enchanting Apparatus",
            "ars_nouveau:enchanting_apparatus",
            "Create a repeatable process for loading pedestal ingredients, supplying Source, and collecting products from the Enchanting Apparatus.",
            44,
            0,
            optional=True,
        )
        .depends_on(relay_network, sustained_ritual)
        .checkmark()
        .finish()
    )

    essence_stockpile = (
        chapter.quest(
            "essence_stockpile",
            "Essences in Reserve",
            "ars_nouveau:manipulation_essence",
            "Maintain a useful stockpile of several magical essence types so advanced glyphs and equipment upgrades do not halt for basic materials.",
            46,
            0,
            optional=True,
        )
        .depends_on(apparatus_automation)
        .checkmark()
        .finish()
    )

    spell_archive = (
        chapter.quest(
            "spell_archive",
            "The Archmage's Spell Archive",
            "ars_nouveau:archmage_spell_book",
            "Create and document a collection of specialized spells for combat, mobility, mining, building, farming, and emergency recovery.",
            44,
            -4,
            optional=True,
        )
        .depends_on(transport_network, familiar_field_test)
        .checkmark()
        .finish()
    )

    defensive_magic = (
        chapter.quest(
            "defensive_magic",
            "Defend the Arcane Grounds",
            "ars_nouveau:spell_turret",
            "Protect a magical outpost using carefully controlled spell turrets, barriers, summons, or utility spells without endangering nearby structures.",
            44,
            5,
            optional=True,
        )
        .depends_on(safe_targeting, remote_source)
        .checkmark()
        .finish()
    )

    unattended_trial = (
        chapter.quest(
            "unattended_magic_trial",
            "Magic That Works Without You",
            "ars_nouveau:source_jar",
            "Leave the expanded workshop operating through a full production cycle. Source generation, storage, transport, and automation should recover without manual intervention.",
            48,
            2,
            optional=True,
        )
        .depends_on(essence_stockpile, defensive_magic)
        .checkmark()
        .finish()
    )

    integrated_workshop = (
        chapter.quest(
            "integrated_archmage_workshop",
            "An Integrated Arcane Complex",
            "ars_nouveau:archmage_spell_book",
            "Connect Source generation, rituals, apparatus crafting, transport, familiars, and turret automation into one coherent magical complex.",
            50,
            0,
            optional=True,
        )
        .depends_on(unattended_trial, spell_archive)
        .checkmark()
        .finish()
    )

    return (
        chapter.quest(
            "archmage_workshop_complete",
            "The Archmage's Living Workshop",
            "ars_nouveau:archmage_spell_book",
            "Your magic is no longer a collection of isolated devices. It is a resilient, automated, and specialized workshop worthy of an archmage.",
            52,
            0,
            optional=True,
        )
        .depends_on(integrated_workshop)
        .checkmark()
        .reward_item("ars_nouveau:source_gem", 24)
        .finish()
    )
