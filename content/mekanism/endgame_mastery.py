from generator.builder import ChapterBuilder


def build_mekanism_endgame_mastery(chapter: ChapterBuilder, stable_reactor: str) -> str:
    plan = (
        chapter.quest(
            "endgame_plan", "Plan the Ultimate Facility", "mekanism:ultimate_induction_cell",
            (
                "Design an optional late-game Mekanism complex with fusion power, massive energy storage, "
                "antimatter production, radioactive logistics, and modular powered equipment."
            ),
            68, 1, optional=True,
        ).depends_on(stable_reactor).checkmark().finish()
    )

    fusion_fuel = (
        chapter.quest(
            "fusion_fuel", "Fuel for a Star", "mekanismgenerators:hohlraum",
            (
                "Produce deuterium and tritium, then prepare a filled Hohlraum. Keep both fuel chains buffered "
                "and verify that every machine can recover safely after a power interruption."
            ),
            70, -5, optional=True,
        ).depends_on(plan).checkmark().finish()
    )
    laser_ignition = (
        chapter.quest(
            "laser_ignition", "Light the Artificial Sun", "mekanism:laser_amplifier",
            (
                "Build a laser array and charge a Laser Amplifier with enough energy to ignite a fusion reactor. "
                "Use redstone control so the ignition system cannot fire accidentally."
            ),
            72, -5, optional=True,
        ).depends_on(fusion_fuel).checkmark().finish()
    )
    fusion_reactor = (
        chapter.quest(
            "fusion_reactor", "Bottle a Star", "mekanismgenerators:fusion_reactor_controller",
            (
                "Assemble and ignite a Fusion Reactor. Start at a conservative injection rate and confirm that "
                "fuel production, heat handling, and energy export remain stable."
            ),
            74, -5, optional=True,
        ).depends_on(laser_ignition).checkmark().finish()
    )
    fusion_trial = (
        chapter.quest(
            "fusion_trial", "Sustained Fusion", "mekanismgenerators:fusion_reactor_port",
            (
                "Run the fusion facility under meaningful load without draining its fuel buffers. Demonstrate "
                "automatic restart procedures and a safe response to interrupted fuel production."
            ),
            76, -5, optional=True,
        ).depends_on(fusion_reactor).checkmark().finish()
    )

    ultimate_matrix = (
        chapter.quest(
            "ultimate_matrix", "A Grid-Sized Battery", "mekanism:ultimate_induction_cell",
            (
                "Expand the Induction Matrix with Ultimate Cells and Providers until it can buffer the output "
                "of the entire power complex and feed peak factory demand."
            ),
            70, -1, optional=True,
        ).depends_on(plan).checkmark().finish()
    )
    power_audit = (
        chapter.quest(
            "power_audit", "Audit Every Watt", "mekanism:network_reader",
            (
                "Measure generation, transfer limits, storage headroom, and major consumers. Remove bottlenecks "
                "and document the order in which nonessential systems should shut down during an emergency."
            ),
            72, -1, optional=True,
        ).depends_on(ultimate_matrix).checkmark().finish()
    )
    black_start = (
        chapter.quest(
            "black_start", "Restart from Darkness", "mekanism:ultimate_energy_cube",
            (
                "Perform a black-start drill using isolated reserve power. Restore fuel production, control "
                "systems, storage, and generation without relying on an already-running main grid."
            ),
            74, -1, optional=True,
        ).depends_on(power_audit).checkmark().finish()
    )

    waste_logistics = (
        chapter.quest(
            "waste_logistics", "Radioactive Logistics", "mekanism:radioactive_waste_barrel",
            (
                "Create a protected, monitored route for nuclear waste, polonium, plutonium, and spent fuel. "
                "Include excess capacity and ensure no single blocked tube can contaminate the main base."
            ),
            70, 4, optional=True,
        ).depends_on(plan).checkmark().finish()
    )
    sps_parts = (
        chapter.quest(
            "sps_parts", "Shape the SPS", "mekanism:sps_casing",
            (
                "Craft the SPS casings, ports, and Supercharged Coils needed to convert polonium into antimatter. "
                "Plan the structure near secure chemical storage and abundant power."
            ),
            72, 4, optional=True,
        ).depends_on(waste_logistics, ultimate_matrix).checkmark().finish()
    )
    sps = (
        chapter.quest(
            "sps", "The Supercritical Phase Shifter", "mekanism:supercharged_coil",
            (
                "Assemble and activate the SPS. Feed it polonium and enough power to maintain production while "
                "keeping all radioactive inputs and outputs isolated."
            ),
            74, 4, optional=True,
        ).depends_on(sps_parts).checkmark().finish()
    )
    antimatter = (
        chapter.quest(
            "antimatter", "Matter's Opposite", "mekanism:pellet_antimatter",
            "Produce your first Antimatter Pellet and store it as a carefully protected strategic resource.",
            76, 4, optional=True,
        ).depends_on(sps).item("mekanism:pellet_antimatter").finish()
    )

    mekasuit = (
        chapter.quest(
            "mekasuit", "Armor of the Machine", "mekanism:mekasuit_bodyarmor",
            (
                "Craft the complete MekaSuit. Charge every piece and treat the suit as a modular platform rather "
                "than finished equipment."
            ),
            70, 9, optional=True,
        ).depends_on(plan).checkmark().finish()
    )
    suit_modules = (
        chapter.quest(
            "suit_modules", "Configure the MekaSuit", "mekanism:module_base",
            (
                "Install a practical set of MekaSuit modules for protection, mobility, vision, breathing, and "
                "energy management. Tune module settings instead of simply enabling everything."
            ),
            72, 9, optional=True,
        ).depends_on(mekasuit).checkmark().finish()
    )
    mekatool = (
        chapter.quest(
            "mekatool", "One Tool, Every Job", "mekanism:meka_tool",
            "Craft a Meka-Tool and install modules suited to mining, construction, and combat.",
            74, 9, optional=True,
        ).depends_on(suit_modules).item("mekanism:meka_tool").finish()
    )
    gear_trial = (
        chapter.quest(
            "gear_trial", "Powered Equipment Trial", "mekanism:meka_tool",
            (
                "Complete a long industrial expedition using the MekaSuit and Meka-Tool. Return with safe energy "
                "reserves and adjust modules that consumed more power than expected."
            ),
            76, 9, optional=True,
        ).depends_on(mekatool).checkmark().finish()
    )

    antimatter_reserve = (
        chapter.quest(
            "antimatter_reserve", "A Strategic Antimatter Reserve", "mekanism:pellet_antimatter",
            "Produce and safely store at least four Antimatter Pellets.",
            78, 4, optional=True,
        ).depends_on(antimatter, fusion_trial).item("mekanism:pellet_antimatter", 4).finish()
    )
    integrated_complex = (
        chapter.quest(
            "integrated_complex", "The Integrated Mekanism Complex", "mekanism:ultimate_control_circuit",
            (
                "Connect fusion, fission backup, induction storage, the SPS, chemical processing, and factories "
                "into one monitored facility with clear isolation boundaries and recovery procedures."
            ),
            78, 0, optional=True,
        ).depends_on(fusion_trial, black_start, antimatter).checkmark().finish()
    )
    industrial_trial = (
        chapter.quest(
            "industrial_trial", "The Seventy-Two-Hour Trial", "mekanism:network_reader",
            (
                "Operate the complete facility unattended for an extended period. No fuel chain may stall, no "
                "waste line may back up, and storage must remain within planned limits."
            ),
            80, 0, optional=True,
        ).depends_on(integrated_complex, gear_trial).checkmark().finish()
    )
    mastery = (
        chapter.quest(
            "mekanism_endgame_mastery", "Master of Matter and Energy", "mekanism:pellet_antimatter",
            (
                "You have controlled fission and fusion, stored power at grid scale, manufactured antimatter, "
                "engineered radioactive logistics, and equipped yourself with Mekanism's finest technology."
            ),
            82, 0, optional=True,
        ).depends_on(industrial_trial, antimatter_reserve).checkmark().reward_item("mekanism:pellet_antimatter").finish()
    )
    return mastery
