from generator.builder import ChapterBuilder


def build_mekanism_factories_advanced_processing(
    chapter: ChapterBuilder, foundations_complete: str
) -> str:
    tier_installer = (
        chapter.quest(
            "tier_installer",
            "Upgrade without Rebuilding",
            "mekanism:basic_tier_installer",
            (
                "Craft a Basic Tier Installer. Tier installers upgrade compatible machines in place, "
                "preserving their inventory and configuration while increasing parallel throughput."
            ),
            20,
            0,
        )
        .depends_on(foundations_complete)
        .item("mekanism:basic_tier_installer", 2)
        .finish()
    )

    basic_factory = (
        chapter.quest(
            "basic_factory",
            "From Machine to Factory",
            "mekanism:basic_smelting_factory",
            (
                "Upgrade a processing machine into a Basic Factory. Factories run several operations "
                "in parallel and are the foundation of a scalable Mekanism production floor."
            ),
            22,
            -3,
        )
        .depends_on(tier_installer)
        .item("mekanism:basic_smelting_factory")
        .finish()
    )

    factory_families = (
        chapter.quest(
            "factory_families",
            "Parallelize the Workshop",
            "mekanism:basic_enriching_factory",
            (
                "Build a second factory type, such as Enriching, Crushing, or Smelting. Match each "
                "factory to the bottleneck in your production line instead of upgrading blindly."
            ),
            24,
            -3,
        )
        .depends_on(basic_factory)
        .checkmark()
        .finish()
    )

    advanced_factory = (
        chapter.quest(
            "advanced_factory",
            "More Operations per Block",
            "mekanism:advanced_smelting_factory",
            (
                "Upgrade one Basic Factory to Advanced tier. Higher tiers add processing slots but also "
                "increase the power and input rate your infrastructure must sustain."
            ),
            26,
            -3,
        )
        .depends_on(factory_families)
        .item("mekanism:advanced_smelting_factory")
        .finish()
    )

    logistical_sorter = (
        chapter.quest(
            "logistical_sorter",
            "Route by Rule",
            "mekanism:logistical_sorter",
            (
                "Craft a Logistical Sorter and use filters to direct different resources into the "
                "correct processing branches. Color channels keep complex transporter networks readable."
            ),
            22,
            3,
        )
        .depends_on(tier_installer)
        .item("mekanism:logistical_sorter")
        .finish()
    )

    transporter_tiers = (
        chapter.quest(
            "transporter_tiers",
            "Feed the Factory Fast Enough",
            "mekanism:advanced_logistical_transporter",
            (
                "Upgrade part of your item network to Advanced Logistical Transporters. Factory speed "
                "is wasted when inputs and outputs cannot move quickly enough."
            ),
            24,
            3,
        )
        .depends_on(logistical_sorter)
        .item("mekanism:advanced_logistical_transporter", 8)
        .finish()
    )

    gas_tank = (
        chapter.quest(
            "chemical_tank",
            "Store the Chemicals",
            "mekanism:basic_chemical_tank",
            (
                "Craft a Basic Chemical Tank for gases and other Mekanism chemicals. Advanced ore "
                "processing depends on stable chemical storage and transport."
            ),
            22,
            7,
        )
        .depends_on(tier_installer)
        .item("mekanism:basic_chemical_tank")
        .finish()
    )

    pressurized_tube = (
        chapter.quest(
            "pressurized_tube",
            "Chemical Pipelines",
            "mekanism:basic_pressurized_tube",
            "Craft Basic Pressurized Tubes and connect a chemical tank to a processing machine.",
            24,
            7,
        )
        .depends_on(gas_tank)
        .item("mekanism:basic_pressurized_tube", 8)
        .finish()
    )

    separator = (
        chapter.quest(
            "electrolytic_separator",
            "Split Water into Gases",
            "mekanism:electrolytic_separator",
            (
                "Build an Electrolytic Separator. With water and power it produces oxygen and hydrogen, "
                "two foundational chemicals for Mekanism processing and energy systems."
            ),
            26,
            7,
        )
        .depends_on(pressurized_tube)
        .item("mekanism:electrolytic_separator")
        .finish()
    )

    purification = (
        chapter.quest(
            "purification_chamber",
            "Purify into Clumps",
            "mekanism:purification_chamber",
            (
                "Craft a Purification Chamber and supply oxygen. This begins three-times ore processing "
                "by converting raw ore into clumps before crushing and enrichment."
            ),
            28,
            3,
        )
        .depends_on(advanced_factory, separator)
        .item("mekanism:purification_chamber")
        .finish()
    )

    triple_processing = (
        chapter.quest(
            "triple_processing",
            "Three Ingots per Ore",
            "mekanism:clump_iron",
            (
                "Complete a Purification Chamber, Crusher, Enrichment Chamber, and Smelter chain. "
                "Process a raw ore through every stage and verify the three-times yield."
            ),
            30,
            3,
        )
        .depends_on(purification, transporter_tiers)
        .checkmark()
        .finish()
    )

    rotary = (
        chapter.quest(
            "rotary_condensentrator",
            "Move between Fluids and Chemicals",
            "mekanism:rotary_condensentrator",
            (
                "Craft a Rotary Condensentrator. It converts supported substances between fluid and "
                "chemical forms, bridging two sides of Mekanism's processing systems."
            ),
            28,
            8,
        )
        .depends_on(separator)
        .item("mekanism:rotary_condensentrator")
        .finish()
    )

    injection = (
        chapter.quest(
            "chemical_injection_chamber",
            "Inject for Greater Yield",
            "mekanism:chemical_injection_chamber",
            (
                "Build a Chemical Injection Chamber. With the correct chemical supply, it advances ore "
                "processing beyond purification and produces shards for the next stage."
            ),
            32,
            1,
        )
        .depends_on(triple_processing, rotary)
        .item("mekanism:chemical_injection_chamber")
        .finish()
    )

    quadruple_processing = (
        chapter.quest(
            "quadruple_processing",
            "Four Ingots per Ore",
            "mekanism:shard_iron",
            (
                "Supply the Chemical Injection Chamber and extend the line through purification, "
                "crushing, enrichment, and smelting. Confirm a four-times ore yield."
            ),
            34,
            1,
        )
        .depends_on(injection)
        .checkmark()
        .finish()
    )

    oxidizer = (
        chapter.quest(
            "chemical_oxidizer",
            "Oxidize Solid Resources",
            "mekanism:chemical_oxidizer",
            "Craft a Chemical Oxidizer to turn supported solid materials into usable chemicals.",
            30,
            10,
        )
        .depends_on(rotary)
        .item("mekanism:chemical_oxidizer")
        .finish()
    )

    chemical_infuser = (
        chapter.quest(
            "chemical_infuser",
            "Combine Chemical Streams",
            "mekanism:chemical_infuser",
            "Craft a Chemical Infuser and combine two chemical inputs into a new processing reagent.",
            32,
            10,
        )
        .depends_on(oxidizer)
        .item("mekanism:chemical_infuser")
        .finish()
    )

    dissolution = (
        chapter.quest(
            "chemical_dissolution_chamber",
            "Dissolve the Ore",
            "mekanism:chemical_dissolution_chamber",
            (
                "Build a Chemical Dissolution Chamber. This is the entry point to five-times processing, "
                "turning ore into slurry with a demanding chemical supply."
            ),
            36,
            5,
        )
        .depends_on(quadruple_processing, chemical_infuser)
        .item("mekanism:chemical_dissolution_chamber")
        .finish()
    )

    washer = (
        chapter.quest(
            "chemical_washer",
            "Wash the Slurry",
            "mekanism:chemical_washer",
            "Craft a Chemical Washer to clean dirty slurry before crystallization.",
            38,
            5,
        )
        .depends_on(dissolution)
        .item("mekanism:chemical_washer")
        .finish()
    )

    crystallizer = (
        chapter.quest(
            "chemical_crystallizer",
            "Crystallize the Product",
            "mekanism:chemical_crystallizer",
            "Craft a Chemical Crystallizer to convert clean slurry into crystals for final processing.",
            40,
            5,
        )
        .depends_on(washer)
        .item("mekanism:chemical_crystallizer")
        .finish()
    )

    five_times = (
        chapter.quest(
            "five_times_processing",
            "Five Ingots per Ore",
            "mekanism:crystal_iron",
            (
                "Connect dissolution, washing, crystallization, injection, purification, crushing, "
                "enrichment, and smelting into one complete chain. Process ore at five-times yield."
            ),
            42,
            5,
        )
        .depends_on(crystallizer)
        .checkmark()
        .finish()
    )

    industrial_mastery = (
        chapter.quest(
            "industrial_processing",
            "A Scalable Industrial Processor",
            "mekanism:elite_enriching_factory",
            (
                "Your factory floor now combines parallel machines, filtered logistics, chemical "
                "handling, and high-yield ore processing. Keep the system balanced, powered, and safe."
            ),
            44,
            1,
        )
        .depends_on(advanced_factory, triple_processing, quadruple_processing, five_times)
        .checkmark()
        .reward_item("mekanism:alloy_reinforced", 8)
        .finish()
    )

    return industrial_mastery
